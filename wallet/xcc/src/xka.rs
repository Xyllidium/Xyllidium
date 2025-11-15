use crate::xhss::XhssKeypair;
use rand::rngs::OsRng;
use rand::RngCore;
use blake3::Hasher;

#[derive(Debug, Clone)]
pub struct XyllKeyManager {
    pub seed: Vec<u8>,
    pub xhss: XhssKeypair,
}

impl XyllKeyManager {
    pub fn new() -> Self {
        let mut seed = vec![0u8; 32];
        OsRng.fill_bytes(&mut seed);

        let mut h = Hasher::new();
        h.update(&seed);
        let seed_hashed = h.finalize().as_bytes().to_vec();

        let xhss = XhssKeypair::generate(&seed_hashed);

        Self { seed, xhss }
    }
}
