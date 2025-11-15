// =============================================
//  XNEE — Xyllidium Neural Entropy Engine
//  High-grade entropy based on CPU jitter,
//  branch-prediction chaos, and timing noise.
// =============================================

use sha3::{Sha3_512, Digest};
use std::time::{Instant};
use rand::Rng;

/// Measure jitter by repeatedly timing tiny operations.
/// The variations in these timings become entropy.
fn jitter_sample() -> u64 {
    let start = Instant::now();

    // Unpredictable loop — CPU-dependent
    let mut x = 0u64;
    for i in 0..500 {
        x = x.wrapping_add(i ^ x.rotate_left((i % 63) as u32));
    }

    let elapsed = start.elapsed().as_nanos() as u64;
    elapsed ^ x
}

/// Collects many jitter samples and mixes them
/// through SHA3-512 to remove bias.
fn collect_jitter_entropy(samples: usize) -> Vec<u8> {
    let mut hasher = Sha3_512::new();

    for _ in 0..samples {
        let s = jitter_sample();
        hasher.update(s.to_le_bytes());
    }

    hasher.finalize().to_vec()
}

/// Random memory noise sampler
fn mem_noise() -> Vec<u8> {
    let mut rng = rand::thread_rng();
    let mut buf = [0u8; 64];
    rng.fill(&mut buf);
    buf.to_vec()
}

/// PUBLIC API
/// Returns N bytes of high-grade entropy.
///
/// This entropy comes from:
///  - CPU jitter
///  - memory noise
///  - SHA3-512 compression
pub fn get_entropy(bytes: usize) -> Vec<u8> {
    let jitter = collect_jitter_entropy(256);
    let memory = mem_noise();

    let mut hasher = Sha3_512::new();
    hasher.update(jitter);
    hasher.update(memory);

    let mut final_hash = hasher.finalize().to_vec();

    // Expand until required size
    while final_hash.len() < bytes {
        let mut h = Sha3_512::new();
        h.update(&final_hash);
        final_hash.extend(h.finalize().to_vec());
    }

    final_hash[..bytes].to_vec()
}
