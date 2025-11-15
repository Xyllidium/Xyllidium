use rand::rngs::OsRng;
use rand::RngCore;
use sha3::{Sha3_512, Digest};

pub fn system_entropy() -> Vec<u8> {
    let mut sys = [0u8; 64];

    let mut rng = OsRng;
    rng.fill_bytes(&mut sys);

    let mut hasher = Sha3_512::new();
    hasher.update(&sys);

    hasher.finalize().to_vec()
}
