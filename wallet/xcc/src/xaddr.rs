use crate::xhss::XmssPublicKey;
use blake3;
use bs58;

///
/// XADDR – Xyllidium Address Format
///
/// Steps:
/// 1. Hash XMSS public key using blake3
/// 2. Take first 32 bytes
/// 3. Add network prefix (0x58 = 'X')
/// 4. Base58 encode
///
pub struct XyllidiumAddress(pub String);

impl XyllidiumAddress {
    pub fn from_xmss(pk: &XmssPublicKey) -> Self {
        // Step 1: Hash raw public key bytes
        let hash = blake3::hash(&pk.pk);

        // Step 2: take first 32 bytes
        let mut digest = hash.as_bytes()[0..32].to_vec();

        // Step 3: prepend network prefix (mainnet = 88 = 'X')
        let mut prefixed = vec![88u8];
        prefixed.append(&mut digest);

        // Step 4: Base58 encode
        let encoded = bs58::encode(prefixed).into_string();

        XyllidiumAddress(encoded)
    }
}
