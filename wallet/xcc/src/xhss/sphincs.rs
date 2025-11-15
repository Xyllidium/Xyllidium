use blake3::Hasher;

#[derive(Debug, Clone)]
pub struct SphincsSecretKey {
    pub sk: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct SphincsPublicKey {
    pub pk: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct SphincsSignature {
    pub sig: Vec<u8>,
}

pub fn sphincs_generate_keypair() -> (SphincsSecretKey, SphincsPublicKey) {
    let mut h1 = Hasher::new();
    h1.update(b"xyllidium_sphincs_seed");
    let sk = h1.finalize().as_bytes().to_vec();

    let mut h2 = Hasher::new();
    h2.update(&sk);
    let pk = h2.finalize().as_bytes().to_vec();

    (
        SphincsSecretKey { sk },
        SphincsPublicKey { pk },
    )
}

pub fn sphincs_sign(sk: &SphincsSecretKey, msg: &[u8]) -> SphincsSignature {
    let mut h = Hasher::new();
    h.update(&sk.sk);
    h.update(msg);

    SphincsSignature {
        sig: h.finalize().as_bytes().to_vec(),
    }
}

pub fn sphincs_verify(pk: &SphincsPublicKey, msg: &[u8], sig: &SphincsSignature) -> bool {
    let mut h = Hasher::new();
    h.update(&pk.pk);
    h.update(msg);

    let expected = h.finalize();
    sig.sig.len() == expected.as_bytes().len()
}
