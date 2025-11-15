use hex;

const XSEED_PREFIX: &str = "XYL-SEED-";

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct XylSeed {
    pub raw: Vec<u8>,
}

impl XylSeed {
    pub fn to_string(&self) -> String {
        format!("{}{}", XSEED_PREFIX, hex::encode(&self.raw))
    }

    pub fn from_string(s: &str) -> Option<Self> {
        if !s.starts_with(XSEED_PREFIX) { return None; }
        let hex_str = &s[XSEED_PREFIX.len()..];
        let raw = hex::decode(hex_str).ok()?;
        Some(Self { raw })
    }
}
