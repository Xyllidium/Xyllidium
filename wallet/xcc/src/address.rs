use blake3::Hasher;
use bs58;

/// Convert public key to a short human-readable address
pub fn address_from_public_key(pk: &[u8]) -> String {
    let mut h = Hasher::new();
    h.update(pk);

    let digest = h.finalize();
    let short = &digest.as_bytes()[0..20];

    format!("XYL-ADDR-{}", bs58::encode(short).into_string())
}
