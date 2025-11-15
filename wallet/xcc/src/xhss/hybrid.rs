use crate::xhss::xmss::*;
use crate::xhss::sphincs::*;

#[derive(Debug, Clone)]
pub struct XhssSignature {
    pub xmss: XmssSignature,
    pub sphincs: SphincsSignature,
}

#[derive(Debug, Clone)]
pub struct XhssKeypair {
    pub xmss: XmssKeypair,
    pub sphincs: (SphincsSecretKey, SphincsPublicKey),
}

impl XhssKeypair {
    pub fn generate(seed: &[u8]) -> Self {
        let xmss = xmss_generate_keypair(seed);
        let sphincs = sphincs_generate_keypair();

        Self { xmss, sphincs }
    }

    pub fn sign(&self, msg: &[u8]) -> XhssSignature {
        let xmss_sig = xmss_sign(&self.xmss.sk, msg);
        let sphincs_sig = sphincs_sign(&self.sphincs.0, msg);

        XhssSignature {
            xmss: xmss_sig,
            sphincs: sphincs_sig,
        }
    }
}
