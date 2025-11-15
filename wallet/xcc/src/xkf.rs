pub const XPRV_PREFIX: &str = "XPRV-";
pub const XPUB_PREFIX: &str = "XPUB-";

#[derive(Debug, Clone)]
pub struct XPrv {
    pub raw: Vec<u8>,  // private key bytes
}

#[derive(Debug, Clone)]
pub struct XPub {
    pub raw: Vec<u8>,  // public key bytes
}

impl XPrv {
    pub fn encode(&self) -> String {
        format!("{}{}", XPRV_PREFIX, hex::encode(&self.raw))
    }
}

impl XPub {
    pub fn encode(&self) -> String {
        format!("{}{}", XPUB_PREFIX, hex::encode(&self.raw))
    }
}
