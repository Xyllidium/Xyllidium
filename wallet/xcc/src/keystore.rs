use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, KeyInit};
use rand::rngs::OsRng;
use rand::RngCore;
use argon2::{Argon2, PasswordHasher};
use password_hash::{SaltString, PasswordHash};
use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct Keystore {
    pub ciphertext: Vec<u8>,
    pub nonce: Vec<u8>,
    pub salt: String,
}

impl Keystore {
    pub fn encrypt(password: &str, plaintext: &[u8]) -> Self {
        // Generate salt
        let mut salt_bytes = [0u8; 16];
        OsRng.fill_bytes(&mut salt_bytes);
        let salt = SaltString::encode_b64(&salt_bytes).unwrap();

        // Argon2 key derivation
        let argon2 = Argon2::default();
        let pw_hash = argon2.hash_password(password.as_bytes(), &salt).unwrap();
        let hash = pw_hash.hash.unwrap();
        let key_bytes = hash.as_bytes().to_vec();

        let key = Key::<Aes256Gcm>::from_slice(&key_bytes);

        // Generate nonce
        let mut nonce_bytes = [0u8; 12];
        OsRng.fill_bytes(&mut nonce_bytes);

        let cipher = Aes256Gcm::new(key);
        let ciphertext = cipher.encrypt(Nonce::from_slice(&nonce_bytes), plaintext).unwrap();

        Keystore {
            ciphertext,
            nonce: nonce_bytes.to_vec(),
            salt: salt.to_string(),
        }
    }

    pub fn decrypt(&self, password: &str) -> Option<Vec<u8>> {
        let salt = SaltString::from_b64(&self.salt).ok()?;

        let argon2 = Argon2::default();
        let pw_hash = argon2.hash_password(password.as_bytes(), &salt).ok()?;
        let hash = pw_hash.hash.unwrap();
        let key_bytes = hash.as_bytes().to_vec();

        let key = Key::<Aes256Gcm>::from_slice(&key_bytes);
        let cipher = Aes256Gcm::new(key);

        cipher.decrypt(Nonce::from_slice(&self.nonce), self.ciphertext.as_ref()).ok()
    }
}
