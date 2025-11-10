use pyo3::prelude::*;
use rand::Rng;

/// Compute entropy for a set of node energy states.
/// Very simple proxy: standard deviation of the values.
#[pyfunction]
fn compute_entropy(energies: Vec<f64>) -> f64 {
    let mean: f64 = energies.iter().sum::<f64>() / energies.len() as f64;
    let variance: f64 = energies.iter().map(|e| (e - mean).powi(2)).sum::<f64>() / energies.len() as f64;
    variance.sqrt()
}

/// Perform one coherence step: adjust node energies to reduce entropy slightly.
#[pyfunction]
fn coherence_step(mut energies: Vec<f64>, k: f64) -> Vec<f64> {
    // get current "entropy" magnitude
    let entropy = compute_entropy(energies.clone());
    let adjustment = entropy * k;

    let mut rng = rand::thread_rng();
    for e in energies.iter_mut() {
        // small random nudge toward equilibrium
        let noise: f64 = rng.gen_range(-adjustment..adjustment);
        *e -= noise;
    }
    energies
}

/// Return system coherence index (0–1 where higher = more coherent)
#[pyfunction]
fn coherence_index(energies: Vec<f64>) -> f64 {
    let entropy = compute_entropy(energies.clone());
    (1.0 / (1.0 + entropy)).min(1.0)
}

/// Python module init
#[pymodule]
fn xcfc(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_entropy, m)?)?;
    m.add_function(wrap_pyfunction!(coherence_step, m)?)?;
    m.add_function(wrap_pyfunction!(coherence_index, m)?)?;
    Ok(())
}
