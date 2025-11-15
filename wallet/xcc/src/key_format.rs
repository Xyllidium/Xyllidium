use blake3;
use bs58;
use hex;

/// Types of keys in Xyllidium wallet
#[derive(Debug, Clone, Copy, serde::Serialize, serde::Deserialize)]
pub enum KeyType {
    Master,
    Public,
    Secret,
}

impl KeyType {
    pub fn prefix(&self) -> &'static str {
        match self {
            KeyType::Master => "XYL-MK-",
            KeyType::Public => "XYL-PK-",
            KeyType::Secret => "XYL-SK-",
        }
    }
}

/// Generic Xyllidium Key Wrapper
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct XKFKey {
    pub key_type: KeyType,
    pub raw: Vec<u8>,
}

impl XKFKey {
    pub fn new(key_type: KeyType, raw: Vec<u8>) -> Self {
        Self { key_type, raw }
    }

    /// Convert to Base58-encoded string
    pub fn to_string(&self) -> String {
        let encoded = bs58::encode(&self.raw).into_string();
        format!("{}{}", self.key_type.prefix(), encoded)
    }

    /// Convert from string → XKFKey
    pub fn from_string(s: &str) -> Option<Self> {
        let (key_type, rest) = if s.starts_with("XYL-MK-") {
            (KeyType::Master, &s[7..])
        } else if s.starts_with("XYL-PK-") {
            (KeyType::Public, &s[7..])
        } else if s.starts_with("XYL-SK-") {
            (KeyType::Secret, &s[7..])
        } else {
            return None;
        };

        let decoded = bs58::decode(rest).into_vec().ok()?;

        Some(Self {
            key_type,
            raw: decoded,
        })
    }
}
