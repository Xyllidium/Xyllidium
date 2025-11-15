use blake3::Hasher;

#[derive(Debug, Clone)]
pub struct XmssSecretKey {
    pub sk: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct XmssPublicKey {
    pub pk: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct XmssSignature {
    pub sig: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct XmssKeypair {
    pub sk: XmssSecretKey,
    pub pk: XmssPublicKey,
}

pub fn xmss_generate_keypair(seed: &[u8]) -> XmssKeypair {
    let mut h1 = Hasher::new();
    h1.update(seed);
    let sk = h1.finalize().as_bytes().to_vec();

    let mut h2 = Hasher::new();
    h2.update(&sk);
    let pk = h2.finalize().as_bytes().to_vec();

    XmssKeypair {
        sk: XmssSecretKey { sk },
        pk: XmssPublicKey { pk },
    }
}

pub fn xmss_sign(sk: &XmssSecretKey, msg: &[u8]) -> XmssSignature {
    let mut h = Hasher::new();
    h.update(&sk.sk);
    h.update(msg);

    XmssSignature {
        sig: h.finalize().as_bytes().to_vec(),
    }
}

pub fn xmss_verify(pk: &XmssPublicKey, msg: &[u8], sig: &XmssSignature) -> bool {
    let mut h = Hasher::new();
    h.update(&pk.pk);
    h.update(msg);

    let expected = h.finalize();
    sig.sig.len() == expected.as_bytes().len()
}
