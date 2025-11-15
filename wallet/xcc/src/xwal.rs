use crate::xka::XyllidiumMasterKey;
use crate::xhss::hybrid::{XhssKeypair, XhssSignature};
use crate::xaddr::XyllidiumAddress;
use crate::keystore::{XKeyStore, save_keystore, load_keystore};
use crate::xnee::get_entropy_256;

#[derive(Debug, Clone)]
pub struct XWallet {
    pub master: XyllidiumMasterKey,
    pub keypair: XhssKeypair,
    pub address: XyllidiumAddress,
}

impl XWallet {

    /// -------------------------------------------------------------
    /// CREATE A NEW WALLET FROM ENTROPY
    /// -------------------------------------------------------------
    pub fn create() -> Self {
        // 1) Collect system entropy
        let entropy = get_entropy_256();

        // 2) Generate master key from entropy
        let master = XyllidiumMasterKey::from_entropy(&entropy);

        // 3) Generate hybrid XMSS+SPHINCS keypair
        let keypair = XhssKeypair::generate(&master.seed);

        // 4) Derive wallet address from public key
        let address = XyllidiumAddress::from_public_key(&keypair.public);

        XWallet { master, keypair, address }
    }

    /// -------------------------------------------------------------
    /// SIGN A MESSAGE WITH HYBRID SIGNATURE
    /// -------------------------------------------------------------
    pub fn sign(&self, message: &[u8]) -> XhssSignature {
        self.keypair.sign(message)
    }

    /// -------------------------------------------------------------
    /// EXPORT TO ENCRYPTED KEYSTORE
    /// -------------------------------------------------------------
    pub fn export(&self, path: &str, password: &str) -> Result<(), String> {
        let keystore = XKeyStore::from_master(&self.master, password)
            .map_err(|e| format!("Keystore error: {:?}", e))?;

        save_keystore(path, &keystore)
            .map_err(|e| format!("Write error: {:?}", e))
    }

    /// -------------------------------------------------------------
    /// IMPORT WALLET FROM KEYSTORE FILE
    /// -------------------------------------------------------------
    pub fn import(path: &str, password: &str) -> Result<Self, String> {
        // 1) Load encrypted file
        let ks = load_keystore(path)
            .map_err(|e| format!("Keystore load failed: {:?}", e))?;

        // 2) Decrypt into master key
        let master = ks.decrypt(password)
            .map_err(|_| "Invalid password".to_string())?;

        // 3) Regenerate deterministic keypair
        let keypair = XhssKeypair::generate(&master.seed);

        // 4) Rebuild address
        let address = XyllidiumAddress::from_public_key(&keypair.public);

        Ok(XWallet { master, keypair, address })
    }
}
