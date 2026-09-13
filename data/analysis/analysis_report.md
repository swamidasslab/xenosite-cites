# Citing-paper analysis

- Citing papers: **777**
- Class counts: {'computational': 245, 'experimental': 350, 'review': 46, 'unknown': 136}
- Predict-then-test (XenoSite use → experiment): {'high': 25, 'low': 149, 'medium': 31} (high+medium=56)
- Topic model docs: **747** across **8** NMF topics
- Pre-2012 citing records (likely metadata noise): **3**

## Classes

Heuristic labels from OpenAlex `type` plus title/abstract keywords (`review` / `experimental` = any wet-lab cue / `computational` = computation-only / `unknown`).

## Predict-then-test

Simple abstract/title detector for papers that **use a XenoSite-family tool to make predictions** and then **test experimentally** (microsomes, LC-MS, in vitro/in vivo, etc.). Benchmark-against-XenoSite papers are excluded. See `predict_then_test.jsonl`.

### High confidence

- 2020 [10.1124/dmd.120.000254] Significance of Multiple Bioactivation Pathways for Meclofenamate as Revealed through Modeling and Reaction Kinetics
- 2022 [10.2174/1389557522666220620125623] Alternative Methods for Pulmonary-Administered Drugs Metabolism: A Breath of Change
- 2019 [10.1002/rcm.8436] In silico , in vitro and in vivo metabolite identification of brexpiprazole using ultra‐high‐performance liquid chromato
- 2019 [10.1002/dta.2725] Update on metabolism of abemaciclib: In silico, in vitro, and in vivo metabolite identification and characterization usi
- 2023 [10.1016/j.heliyon.2023.e17058] Reactive intermediates formation and bioactivation pathways of spebrutinib revealed by LC-MS/MS: In vitro and in silico 
- 2026 [10.1021/acs.chemrestox.6c00107] Physicochemical Characterization and Metabolites Identification of the Synthetic Cannabinoid MDMB-5′Br-PINACA Using In S
- 2019 [10.2174/1386207322666190705143322] Molecular Docking Supplements an In vitro Determination of the Leading CYP Isoform for Arylpiperazine Derivatives
- 2020 [10.3390/molecules25215004] Identification of Iminium Intermediates Generation in the Metabolism of Tepotinib Using LC-MS/MS: In Silico and Practica
- 2022 [10.1002/rcm.9335] Comprehensive metabolite identification study of arterolane using hydrophilic interaction liquid chromatography with qua
- 2023 [10.59957/jctm.v58i3.94] Computational predictions of site of metabolism of a pyrrolebased compound as a potential antitubercular agent
- 2023 [10.3390/separations10060353] In Vitro and Reactive Metabolites Investigation of Metabolic Profiling of Tyrosine Kinase Inhibitors Dubermatinib in HLM
- 2017 [10.4155/fmc-2017-0126] In Vitro Metabolism Study of a Novel P38 Kinase Inhibitor: In Silico Predictions, Structure Elucidation Using MS/MS-I
- 2021 [10.1186/s12859-021-04363-6] Constructing xenobiotic maps of metabolism to predict enzymes catalyzing metabolites capable of binding to DNA
- 2019 [10.1021/acs.chemrestox.9b00006] CYP2C19 and 3A4 Dominate Metabolic Clearance and Bioactivation of Terbinafine Based on Computational and Experimental Ap
- 2021 [10.21203/rs.3.rs-157802/v1] Constructing Xenobiotic Maps of Metabolism to Predict the Role of Enzymes in DNA Adduct Formation
- 2026 [10.1016/j.insi.2026.100193] Artificial intelligence and in silico study using De Novo drug design to explore molecular targets of Burkholderia pseud
- 2026 [10.3389/fbinf.2026.1856040] Computational validation and network pharmacology reveal the cardioprotective and hypolipidemic potential of Arisaema Ja
- 2019 [10.11603/mcch.2410-681x.2019.v.i3.10558] IN SILICO ДОСЛІДЖЕННЯ МОЖЛИВИХ ШЛЯХІВ МЕТАБОЛІЗМУ АТРИСТАМІНУ В ОРГАНІЗМІ ЛЮДИНИ
- 2020 [10.1039/c9ra10871h] Identification and characterization of in silico , in vivo , in vitro , and reactive metabolites of infigratinib using L
- 2020 [10.1039/d0ra01624a] In silico and in vitro metabolism of ribociclib: a mass spectrometric approach to bioactivation pathway elucidation and 
- 2021 [10.1002/bmc.5082] Metabolite profiling of IMID‐2, a novel anticancer molecule of piperazine derivative: In silico prediction, in vitro and
- 2019 [10.1016/j.bcp.2019.113661] Comprehensive kinetic and modeling analyses revealed CYP2C9 and 3A4 determine terbinafine metabolic clearance and bioact
- 2023 [10.1007/s00210-023-02413-9] Piperazine ring toxicity in three novel anti-breast cancer drugs: an in silico and in vitro metabolic bioactivation appr
- 2018 [10.1016/j.bcp.2018.07.043] Lamisil (terbinafine) toxicity: Determining pathways to bioactivation through computational and experimental approaches
- 2024 [10.3390/toxics12120931] Development of a Predictive Model for N-Dealkylation of Amine Contaminants Based on Machine Learning Methods

## Topics

- **T0** (n=100): metabolism, prediction, models, som, p450, drug, cyp, site
- **T1** (n=80): deep, deep learning, neural, learning, networks, network, neural networks, neural network
- **T2** (n=117): molecular, docking, molecular docking, compounds, binding, potential, study, simulations
- **T3** (n=81): drug, discovery, ai, drug discovery, artificial, intelligence, artificial intelligence, design
- **T4** (n=80): metabolites, ms, vitro, mass, vivo, mass spectrometry, spectrometry, reactive
- **T5** (n=188): activity, synthesis, cell, cells, anticancer, derivatives, compounds, cancer
- **T6** (n=64): learning, machine, machine learning, small, ml, prediction, quantum, molecules
- **T7** (n=37): adme, adme profile, silico, profile, forensic, excretion, metabolism excretion, cas

## Figures

See `docs/figures/` (committed) and `artifacts/analysis/figures/`.

