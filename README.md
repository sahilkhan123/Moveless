# Moveless: Minimizing Overhead on QCCDs via Versatile Execution and Low Excess Shuttling

> **Moveless** is a QCCD compiler that significantly improves logical error rates for **stabilizer codes** when deployed on real hardware.  
> It is **topology-agnostic** and can be run on flexibly tuned hardware architectures.

A full walkthrough of the compiler and usage instructions is available in [`moveless_example.ipynb`](moveless_example.ipynb).  
A supplemental demonstration focused on color code decoding is provided in [`color_codes_decoding.ipynb`](color_codes_decoding.ipynb).

**Moveless** is built on top of the open-source [QCCDSim simulator](https://github.com/prakashmurali/QCCDSim) by *Murali et al.*,  
which enables flexible control over:

- Trap topology  
- Capacity constraints  
- Gate types  
- And other hardware-specific parameters

The core logic for dynamic stabilizer scheduling and mapping is implemented in:

- `ejf_schedule.py` – dynamic execution schedule generation  
- `customScheduler.py` – flexible mapping of operations to hardware

---

## How to Cite

If you use **Moveless** in your research, please cite:

> *Moveless: Minimizing Overhead on QCCDs via Versatile Execution and Low Excess Shuttling*  
> Sahil Khan, Suhas Vittal, Kenneth Brown, Jonathan Baker  
> arXiv:2508.03914 [quant-ph], 2025  
> [https://arxiv.org/abs/2508.03914](https://arxiv.org/abs/2508.03914)

```bibtex
@misc{khan2025movelessminimizingoverheadqccds,
  title        = {Moveless: Minimizing Overhead on QCCDs via Versatile Execution and Low Excess Shuttling},
  author       = {Sahil Khan and Suhas Vittal and Kenneth Brown and Jonathan Baker},
  year         = {2025},
  eprint       = {2508.03914},
  archivePrefix= {arXiv},
  primaryClass = {quant-ph},
  url          = {https://arxiv.org/abs/2508.03914}
}

If you also make use of the underlying simulator, please additionally cite:

> *Architecting Noisy Intermediate-Scale Trapped Ion Quantum Computers*
> Prakash Murali, Dripto M. Debroy, Kenneth R. Brown, Margaret Martonosi
> arXiv:2004.04706 [quant-ph], 2020
> [https://arxiv.org/abs/2004.04706](https://arxiv.org/abs/2004.04706)

```bibtex
@misc{murali2020architectingnoisyintermediatescaletrapped,
  title        = {Architecting Noisy Intermediate-Scale Trapped Ion Quantum Computers},
  author       = {Prakash Murali and Dripto M. Debroy and Kenneth R. Brown and Margaret Martonosi},
  year         = {2020},
  eprint       = {2004.04706},
  archivePrefix= {arXiv},
  primaryClass = {quant-ph},
  url          = {https://arxiv.org/abs/2004.04706}
}