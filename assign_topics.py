#!/usr/bin/env python3
"""
NEET Topic Classifier
Reads the topic taxonomy from ALLEN's distribution tables (pages 7-9 of the PDF)
and assigns topic + subtopic to every question in questions.json via keyword matching.

Output:
  topics.json   — {year: {topic: [q_numbers]}}
  questions.json — enriched with "topic" and "subtopic" fields (updated in place)
"""

import json, re
from pathlib import Path
from collections import defaultdict

QUESTIONS_JSON = Path("questions.json")
TOPICS_JSON    = Path("topics.json")

# ─────────────────────────────────────────────────────────────────────────────
# TOPIC TAXONOMY
# Each entry: (topic_name, subject, subtopic, keyword_list)
# Rules are checked IN ORDER — put more-specific topics first.
# A question scores +1 per matched keyword; highest scorer wins per subject.
# ─────────────────────────────────────────────────────────────────────────────

RULES = [

    # ══════════════════════════════════════════════════════
    # PHYSICS  (Q 1-45)
    # ══════════════════════════════════════════════════════

    ("Modern Physics", "Physics", "Photoelectric Effect",
     ["photoelectric", "photon", "work function", "threshold frequency",
      "de broglie", "matter wave", "compton", "photoelectron"]),

    ("Modern Physics", "Physics", "Nuclear Physics",
     ["radioactiv", "half.life", "decay constant", "alpha", "beta", "gamma ray",
      "nucleus", "binding energy", "mass defect", "nuclear fission", "nuclear fusion",
      "radioactive", "activity", "disintegration", "uranium", "neutron", "proton"]),

    ("Modern Physics", "Physics", "Atoms and Bohr Model",
     ["bohr", "energy level", "hydrogen spectrum", "rydberg", "balmer", "lyman",
      "paschen", "brackett", "atomic spectrum", "wavelength of light absorbed",
      "excitation", "ionization energy of hydrogen", "transition n ="]),

    ("Semiconductor Electronics", "Physics", "Logic Gates and Circuits",
     ["logic gate", "AND gate", "OR gate", "NOT gate", "NAND", "NOR", "XOR",
      "logic implementation", "output.*gate", "gate.*output",
      "boolean", "truth table", "output y"]),

    ("Semiconductor Electronics", "Physics", "Diodes and Transistors",
     ["p-n junction", "diode", "zener", "transistor", "rectifier", "forward bias",
      "reverse bias", "semiconductor", "n-type", "p-type", "depletion layer",
      "full wave rectifier", "half wave"]),

    ("Electromagnetic Waves", "Physics", "EM Spectrum",
     ["electromagnetic wave", "em wave", "electric field.*magnetic field",
      "magnetic field.*electric field", "maxwell", "poynting", "intensity of em",
      "electromagnetic spectrum", "infrared", "ultraviolet", "microwave",
      "e_z", "b_y", "e0", "b0", "plane wave"]),

    ("Wave Optics", "Physics", "Interference and Diffraction",
     ["interference", "diffraction", "fringe width", "young.s double slit",
      "path difference", "coherent", "polariz", "brewster", "malus",
      "single slit", "double slit", "central maxima"]),

    ("Geometrical Optics", "Physics", "Lens and Mirror",
     ["lens", "mirror", "focal length", "magnification", "image distance",
      "object distance", "refractive index", "refraction", "snell",
      "total internal reflection", "critical angle", "concave", "convex",
      "eye piece", "objective", "microscope", "telescope", "magnifying"]),

    ("Alternating Current", "Physics", "AC Circuits",
     ["alternating current", "rms", "impedance", "resonan", "lcr", "l-c-r",
      "inductive reactance", "capacitive reactance", "phase difference",
      "transformer", "power factor", "ac circuit", "inductor.*capacitor"]),

    ("Electromagnetic Induction", "Physics", "Faraday and Lenz",
     ["electromagnetic induction", "faraday", "lenz", "induced emf",
      "flux linkage", "mutual inductance", "self inductance", "eddy current",
      "induced current", "changing flux", "motional emf"]),

    ("Magnetic Effects of Current", "Physics", "Biot-Savart and Ampere",
     ["biot.savart", "ampere", "solenoid", "toroid", "magnetic field due to",
      "circular loop.*magnetic", "magnetic field at centre",
      "moving charge in magnetic", "cyclotron"]),

    ("Magnetic Effects of Current", "Physics", "Magnetism and Moving Charges",
     ["magnetic moment", "bar magnet", "dipole", "hysteresis", "permeability",
      "diamagnetic", "paramagnetic", "ferromagnetic", "torque on dipole",
      "force on moving charge", "velocity selector", "lorentz force",
      "magnetic force on conductor"]),

    ("Current Electricity", "Physics", "Circuits and Laws",
     ["kirchhoff", "wheatstone", "metre bridge", "potentiometer",
      "internal resistance", "emf of battery", "current.*circuit", "current.*battery", "current through battery",
      "constant voltage", "potential difference", "va.*vb", "vb.*va",
      "point.*circuit", "circuit.*figure",
      "resistivity", "drift velocity", "mobility", "colour code",
      "equivalent resistance", "combination of resistors", "power dissipated",
      "heat generated", "ohm.s law", "r = v/i", "electric circuit"]),

    ("Current Electricity", "Physics", "Resistance and Ohm's Law",
     ["resistance", "resistor", "conductance", "ohmic", "non-ohmic",
      "specific resistance", "wire.*resistance", "resistance of wire"]),

    ("Electrostatics", "Physics", "Capacitors",
     ["capacitor", "capacitance", "dielectric", "electric displacement",
      "parallel plate capacitor", "spherical capacitor", "energy stored in capacitor",
      "charging of capacitor"]),

    ("Electrostatics", "Physics", "Electric Field and Potential",
     ["coulomb", "electric field", "electric potential", "equipotential",
      "gauss.s law", "electric flux", "charge distribution", "dipole",
      "surface charge density", "linear charge", "point charge",
      "electrostatic", "potential energy of charge"]),

    ("Thermal Physics", "Physics", "Heat Transfer",
     ["thermal conductivity", "rate of heat", "heat transfer", "conduction",
      "convection", "radiation", "stefan", "newton.s law of cooling",
      "temperature gradient", "thermal resistance", "wein.s"]),

    ("Thermal Physics", "Physics", "Thermodynamics",
     ["first law of thermodynamics", "second law", "carnot", "efficiency",
      "isothermal", "adiabatic", "isochoric", "isobaric", "entropy",
      "heat engine", "refrigerator", "cop", "internal energy",
      "work done by gas", "pv diagram", "cyclic process"]),

    ("Kinetic Theory of Gases", "Physics", "Ideal Gas Laws",
     ["kinetic theory", "ideal gas", "rms speed", "mean free path",
      "moles of.*gas", "cylinder.*volume", "gas.*withdrawn", "gas.*moles",
      "degree of freedom", "equipartition", "van der waals",
      "pressure of gas", "temperature.*kinetic", "boltzmann"]),

    ("Oscillations", "Physics", "Simple Harmonic Motion",
     ["simple harmonic", "shm", "time period of.*spring", "oscillat",
      "amplitude", "restoring force", "angular frequency", "pendulum",
      "spring-mass", "spring constant", "displacement.*sin", "x = a sin",
      "x = a cos"]),

    ("Waves", "Physics", "Sound Waves",
     ["sound", "frequency of sound", "doppler", "beats", "resonan.*pipe", "fundamental frequency", "pipe.*dipped",
      "open pipe", "closed pipe", "pipe.*water", "standing wave", "node", "antinode",
      "organ pipe", "string.*vibrat", "harmonics"]),

    ("Waves", "Physics", "Wave Motion",
     ["wave", "wavelength", "wave velocity", "wave equation", "transverse wave",
      "longitudinal wave", "progressive wave", "superposition"]),

    ("Gravitation", "Physics", "Gravitation",
     ["gravitational", "escape velocity", "orbital velocity", "satellite",
      "kepler", "gravitational potential", "acceleration due to gravity",
      "geostationary", "weight.*planet", "planets", "gravitation",
      "period of revolution", "orbital.*radius", "radius.*orbit",
      "kepler.s third", "sun.*rotates", "martian orbit", "time period.*orbit"]),

    ("Rotational Motion", "Physics", "Rotation and Rigid Body",
     ["moment of inertia", "angular momentum", "torque", "rolling",
      "rotational kinetic", "angular velocity", "angular acceleration",
      "radius of gyration", "rigid body", "rotation", "theorem of axes"]),

    ("Properties of Matter", "Physics", "Fluid Mechanics",
     ["viscosity", "stokes", "terminal velocity", "bernoulli", "fluid",
      "surface tension", "capillary", "excess pressure", "pressure in liquid",
      "hydraulic", "angle of contact"]),

    ("Properties of Matter", "Physics", "Elasticity",
     ["young.s modulus", "bulk modulus", "modulus of rigidity",
      "stress", "strain", "elastic", "breaking stress", "elongation"]),

    ("Work, Energy and Power", "Physics", "Work Energy Theorem",
     ["kinetic energ", "potential energ", "work done", "work-energy",
      "conservation of energy", "power", "work.energy theorem",
      "fa/fb", "force.*stops", "stopping distance", "coefficient of restitution",
      "elastic collision", "inelastic collision", "collision"]),

    ("Laws of Motion", "Physics", "Newton's Laws",
     ["newton", "friction", "inertia", "normal reaction", "free body",
      "inclined plane", "atwood", "pseudo force", "circular motion",
      "centripetal", "banking", "conical pendulum"]),

    ("Kinematics", "Physics", "Motion in Plane",
     ["projectile", "relative velocity", "relative motion", "river boat",
      "motion in two", "2d motion", "horizontal projectile"]),

    ("Kinematics", "Physics", "Motion in Straight Line",
     ["velocity", "acceleration", "uniform.*acceleration", "free fall",
      "equations of motion", "displacement.*time", "v = u + at",
      "speed", "distance", "average velocity", "retardation"]),

    ("Units and Measurement", "Physics", "Dimensions and Errors",
     ["dimensional", "dimension", "significant figure", "error", "least count",
      "vernier", "screw gauge", "parallax", "accuracy", "precision",
      "fundamental unit", "msd", "vsd"]),

    # ══════════════════════════════════════════════════════
    # CHEMISTRY  (Q 46-90)
    # ══════════════════════════════════════════════════════

    ("Electrochemistry", "Chemistry", "Electrolysis and Faraday",
     ["electrolysis", "faraday.s law", "electrodeposition", "electrode",
      "cathode", "anode", "electroplating", "coulometer"]),

    ("Electrochemistry", "Chemistry", "Electrochemical Cells",
     ["cell potential", "emf", "standard electrode", "reduction potential",
      "oxidation potential", "nernst", "galvanic cell", "daniel cell",
      "electrochemical", "e°cell", "ecell"]),

    ("Electrochemistry", "Chemistry", "Conductance",
     ["molar conductivity", "equivalent conductance", "kohlrausch",
      "conductance", "conductivity", "degree of dissociation.*conductance",
      "lambda_m", "λm"]),

    ("Chemical Kinetics", "Chemistry", "Rate Laws",
     ["rate of reaction", "order of reaction", "rate constant",
      "rate law", "pseudo first", "half.life", "activation energy",
      "arrhenius", "pre-exponential", "molecularity", "rate expression"]),

    ("Thermodynamics", "Chemistry", "Thermochemistry",
     ["enthalpy", "hess.s law", "bond dissociation", "lattice energy",
      "heat of formation", "heat of combustion", "calorimetry",
      "born-haber", "△h", "∆h", "standard enthalpy"]),

    ("Thermodynamics", "Chemistry", "Entropy and Gibbs Energy",
     ["entropy", "gibbs", "△g", "∆g", "spontaneous", "second law.*thermo",
      "free energy", "equilibrium constant.*gibbs"]),

    ("Equilibrium", "Chemistry", "Chemical Equilibrium",
     ["equilibrium constant", "kc", "kp", "le chatelier", "degree of dissociation",
      "degree of ionization", "kp.*kc", "equilibrium.*concentration",
      "forward reaction rate", "backward reaction rate"]),

    ("Equilibrium", "Chemistry", "Ionic Equilibrium",
     ["ph", "poh", "buffer", "henderson", "solubility product", "ksp",
      "common ion", "hydrolysis", "salt of weak", "degree of hydrolysis",
      "acid.*base", "ionization of weak", "weak acid", "weak base",
      "strong acid", "strong base", "ka", "kb"]),

    ("Solutions", "Chemistry", "Colligative Properties",
     ["colligative", "van't hoff", "osmotic pressure", "elevation in boiling",
      "depression in freezing", "raoult.s law", "relative lowering",
      "molal elevation", "ebullioscopic", "cryoscopic", "abnormal"]),

    ("Solutions", "Chemistry", "Types of Solutions",
     ["mole fraction", "molality", "molarity", "normality", "henry.s law",
      "solubility.*gas", "vapour pressure", "ideal solution",
      "non-ideal solution", "azeotrope", "partial pressure"]),

    ("Solid State", "Chemistry", "Crystal Systems",
     ["unit cell", "bcc", "fcc", "hcp", "ccp", "crystal system",
      "packing efficiency", "coordination number.*crystal",
      "edge length", "radius.*ion", "crystal lattice", "ionic crystal"]),

    ("Solid State", "Chemistry", "Defects",
     ["schottky", "frenkel", "interstitial defect", "impurity defect",
      "point defect", "metal excess", "metal deficiency"]),

    ("Surface Chemistry", "Chemistry", "Colloids",
     ["colloid", "tyndall", "brownian", "sol", "gel", "emulsion",
      "lyophilic", "lyophobic", "coagulation", "peptization",
      "zeta potential", "dialysis"]),

    ("Surface Chemistry", "Chemistry", "Adsorption",
     ["adsorption", "freundlich", "langmuir", "adsorbate", "adsorbent",
      "physisorption", "chemisorption", "catalysis.*surface"]),

    ("Coordination Compounds", "Chemistry", "Werner and Nomenclature",
     ["coordination compound", "werner", "complex.*ion", "ligand",
      "chelate", "ambidentate", "coordination number.*complex",
      "oxidation state.*complex", "counter ion", "coordination sphere"]),

    ("Coordination Compounds", "Chemistry", "Crystal Field Theory",
     ["crystal field", "cfse", "cft", "d orbital splitting", "high spin",
      "low spin", "delta_o", "spectrochemical", "strong field", "weak field"]),

    ("Coordination Compounds", "Chemistry", "Isomerism in Complexes",
     ["linkage isomer", "ionization isomer", "geometric isomer.*complex",
      "optical isomer.*complex", "coordinate isomer"]),

    ("p-Block Elements", "Chemistry", "Group 15-17",
     ["nitrogen", "phosphorus", "oxygen", "sulphur", "chlorine",
      "halogens", "interhalogen", "oxoacid", "ozone", "allotrope.*sulphur",
      "allotrope.*phosphorus", "basicity of.*amine", "ammonia",
      "h2so4", "hno3", "h3po4", "hcl", "bleaching"]),

    ("p-Block Elements", "Chemistry", "Group 13-14",
     ["boron", "aluminium", "silicon", "carbon allotrope", "graphite",
      "diamond", "fullerene", "silicate", "borazine", "diborane",
      "group 13", "group 14"]),

    ("d and f Block Elements", "Chemistry", "Transition Metals",
     ["transition metal", "d-block", "variable oxidation state",
      "paramagnetic.*d-block", "ferromagnet", "catalytic.*transition", "colored compound",
      "potassium permanganate", "potassium dichromate", "chromate",
      "manganate", "dichromate", "kmno4", "k2cr2o7"]),

    ("d and f Block Elements", "Chemistry", "Lanthanides and Actinides",
     ["lanthanide", "lanthanoid", "actinide", "actinoid",
      "lanthanide contraction", "f-block"]),

    ("s-Block Elements", "Chemistry", "Alkali and Alkaline Earth Metals",
     ["alkali metal", "alkaline earth", "group 1", "group 2",
      "sodium", "potassium", "calcium", "magnesium", "lithium",
      "plaster of paris", "gypsum", "cation analysis", "group.*cation",
      "caustic soda", "washing soda",
      "baking soda", "down.s process", "castner"]),

    ("Hydrogen", "Chemistry", "Hydrogen and its Compounds",
     ["hydrogen bond", "heavy water", "hydrogen peroxide", "h2o2",
      "ortho hydrogen", "para hydrogen", "hydride", "water.*anomalous"]),

    ("Environmental Chemistry", "Chemistry", "Pollution",
     ["pollution", "smog", "acid rain", "greenhouse", "ozone depletion",
      "bod", "cod", "eutrophication", "pesticide", "deforestation",
      "green chemistry", "cfcs", "freons", "global warming"]),

    ("Atomic Structure", "Chemistry", "Quantum Mechanics",
     ["quantum number", "orbital", "aufbau", "hund", "pauli",
      "electronic configuration", "shape of orbital",
      "dalton", "atomic theory", "effective nuclear charge", "shielding", "screening",
      "de broglie.*electron", "heisenberg", "schrodinger",
      "radial distribution"]),

    ("Atomic Structure", "Chemistry", "Bohr Model",
     ["bohr.s model.*hydrogen", "radius.*bohr", "energy.*bohr",
      "velocity.*electron.*orbit", "rydberg.*chemistry",
      "emission spectrum of hydrogen", "atomic number.*element"]),

    ("Chemical Bonding", "Chemistry", "Molecular Orbital Theory",
     ["molecular orbital", "mot", "bonding orbital", "antibonding",
      "bond order", "sigma bond", "pi bond", "homo", "lumo",
      "diamagnetic.*molecule", "paramagnetic.*molecule"]),

    ("Chemical Bonding", "Chemistry", "VSEPR and Hybridization",
     ["hybridization", "vsepr", "shape of molecule", "geometry of molecule",
      "lone pair", "bond angle", "sp3", "sp2", "sp", "sp3d",
      "sp3d2", "dsp2", "linear.*molecule", "trigonal", "tetrahedral",
      "octahedral", "bent", "see-saw", "t-shape", "square planar",
      "dipole moment"]),

    ("Chemical Bonding", "Chemistry", "Ionic and Covalent Bonds",
     ["ionic bond", "covalent bond", "polar covalent", "electronegativity",
      "fajan.s rule", "lattice energy.*bonding", "hydrogen bonding",
      "van der waals.*bonding", "ionic character", "bond polarity"]),

    ("Mole Concept", "Chemistry", "Stoichiometry",
     ["mole", "avogadro", "stoichiometry", "limiting reagent",
      "percent yield", "empirical formula", "molecular formula",
      "equivalent weight", "normality.*equivalent",
      "number of moles", "molar mass"]),

    ("Isomerism", "Chemistry", "Stereoisomerism",
     ["stereoisomer", "enantiomer", "diastereomer", "meso",
      "chiral", "achiral", "optical activity", "r-s configuration",
      "e-z configuration", "cis-trans", "geometric isomer",
      "optical isomer", "plane of symmetry"]),

    ("Isomerism", "Chemistry", "Structural Isomerism",
     ["structural isomer", "chain isomer", "position isomer",
      "functional isomer", "metamers", "tautomer"]),

    ("General Organic Chemistry", "Chemistry", "Reaction Mechanisms",
     ["inductive effect", "mesomeric", "resonance.*organic",
      "hyperconjugation", "electrophile", "nucleophile",
      "sn1", "sn2", "e1", "e2", "lassaigne", "carbocation", "carbanion",
      "free radical", "rearrangement", "markovnikov",
      "anti-markovnikov", "peroxide effect"]),

    ("General Organic Chemistry", "Chemistry", "IUPAC Nomenclature",
     ["iupac", "nomenclature", "name of compound", "correct iupac",
      "systematic name"]),

    ("Hydrocarbons", "Chemistry", "Aromatic Compounds",
     ["benzene", "aromatic", "toluene", "naphthalene", "aniline",
      "nitrobenzene", "electrophilic aromatic", "friedel-crafts",
      "resonance.*benzene", "huckel", "deactivating", "activating group"]),

    ("Hydrocarbons", "Chemistry", "Alkenes and Alkynes",
     ["alkene", "alkyne", "addition reaction", "hydrogenation",
      "halogenation", "hydration", "ozonolysis", "polymerization.*alkene",
      "hbr.*alkene", "baeyer.s test", "bromine water", "decolouris", "decoloriz", "acetylene", "ethylene",
      "propylene", "conjugated diene", "diels-alder"]),

    ("Hydrocarbons", "Chemistry", "Alkanes",
     ["alkane", "methane", "ethane", "propane", "halogenation.*alkane",
      "free radical substitution", "combustion.*alkane"]),

    ("Haloalkanes and Haloarenes", "Chemistry", "Halo Compounds",
     ["haloalkane", "haloarene", "grignard", "wurtz", "finkelstein",
      "swarts", "nucleophilic substitution.*halo",
      "chlorobenzene", "vinyl chloride", "methyl iodide",
      "alkyl halide", "aryl halide"]),

    ("Alcohols, Phenols and Ethers", "Chemistry", "Alcohols and Phenols",
     ["alcohol", "phenol", "ether", "dehydration", "esterification",
      "lucas test", "victor meyer", "reimer-tiemann",
      "kolbe.s reaction", "schotten-baumann",
      "acidity of phenol", "phenoxide"]),

    ("Aldehydes, Ketones and Carboxylic Acids", "Chemistry", "Aldehyde and Ketone Reactions",
     ["aldehyde", "ketone", "carbonyl", "nucleophilic addition",
      "aldol", "cannizzaro", "tollen.s", "fehling", "benedict",
      "clemmensen", "wolf-kishner", "crossed aldol", "mgbr", "grignard.*product", "suitable reagent", "reagent.*conversion", "och3",
      "2,4-dnp", "oxime"]),

    ("Aldehydes, Ketones and Carboxylic Acids", "Chemistry", "Carboxylic Acids",
     ["carboxylic acid", "formic", "acetic", "propionic",
      "decarboxylation", "kolbe electrolysis", "hell-volhard",
      "amide", "acid chloride", "anhydride", "ester",
      "saponification"]),

    ("Amines", "Chemistry", "Amines and Diazonium",
     ["amine", "primary amine", "secondary amine", "tertiary amine",
      "basicity.*amine", "hinsberg", "gabriel", "hofmann",
      "diazonium", "coupling reaction", "azo dye", "aniline",
      "acetylation.*amine"]),

    ("Biomolecules", "Chemistry", "Carbohydrates",
     ["carbohydrate", "glucose", "fructose", "sucrose", "lactose",
      "maltose", "starch", "glycogen", "cellulose",
      "reducing sugar", "non-reducing sugar", "mutarotation",
      "anomeric", "pyranose", "furanose", "monosaccharide",
      "disaccharide", "polysaccharide", "glycosidic bond"]),

    ("Biomolecules", "Chemistry", "Proteins and Enzymes",
     ["protein", "amino acid", "peptide bond", "denaturation",
      "primary structure", "secondary structure", "alpha helix",
      "beta sheet", "enzyme", "active site", "coenzyme",
      "zwitter ion", "isoelectric"]),

    ("Biomolecules", "Chemistry", "Nucleic Acids and Vitamins",
     ["nucleic acid", "dna.*chemistry", "rna.*chemistry", "nucleotide",
      "nucleoside", "adenosine", "adenylic acid", "purine", "pyrimidine", "adenine", "guanine",
      "cytosine", "thymine", "uracil", "vitamin", "ascorbic"]),

    ("Polymers", "Chemistry", "Types of Polymers",
     ["polymer", "monomer", "addition polymer", "condensation polymer",
      "nylon", "teflon", "pvc", "polythene", "polyester",
      "bakelite", "rubber", "vulcanization", "buna", "neoprene",
      "thermoplastic", "thermosetting", "degree of polymerization"]),

    ("Chemistry in Everyday Life", "Chemistry", "Drugs and Detergents",
     ["drug", "analgesic", "antibiotic", "antiseptic", "disinfectant",
      "antacid", "antihistamine", "tranquilizer", "detergent",
      "soap", "cleansing action", "dye", "food preservative",
      "artificial sweetener", "saccharin", "aspartame"]),

    ("Redox Reactions", "Chemistry", "Oxidation-Reduction",
     ["oxidation state", "oxidation number", "redox", "reducing agent",
      "oxidizing agent", "disproportionation", "balancing redox",
      "half reaction"]),

    ("Metallurgy", "Chemistry", "Extraction of Metals",
     ["metallurgy", "ores", "gangue", "flux", "slag",
      "calcination", "roasting", "smelting", "electrolytic reduction",
      "hall-heroult", "van arkel", "zone refining", "froth flotation",
      "leaching", "bauxite", "haematite", "galena"]),

    # ══════════════════════════════════════════════════════
    # BIOLOGY  (Q 91-180)
    # ══════════════════════════════════════════════════════

    ("Molecular Basis of Inheritance", "Biology", "Replication and Transcription",
     ["replication", "transcription", "translation", "semi-conservative",
      "okazaki fragment", "dna polymerase", "rna polymerase",
      "promoter", "template strand", "coding strand", "histone",
      "chromosome.*gene", "gene.*chromosome", "highest number of genes",
      "adenosine.*nucleoside", "adenylic.*nucleotide", "nucleoside.*nucleotide",
      "nitrogen base.*nucleoside",
      "meselson.*stahl", "central dogma"]),

    ("Molecular Basis of Inheritance", "Biology", "Genetic Code and Gene Expression",
     ["codon", "anticodon", "genetic code", "start codon", "stop codon",
      "trna", "mrna", "rrna", "ribosome.*translation",
      "lac operon", "operon", "inducible", "repressible",
      "post-translational", "splicing", "intron", "exon"]),

    ("Principles of Inheritance", "Biology", "Mendel's Laws",
     ["mendel", "monohybrid", "dihybrid", "law of segregation",
      "law of independent", "dominant", "recessive", "phenotype",
      "genotype", "homozygous", "heterozygous", "f1", "f2",
      "punnett square", "test cross", "back cross"]),

    ("Principles of Inheritance", "Biology", "Chromosomal Basis",
     ["linkage", "crossing over", "recombination frequency",
      "chromosomal map", "sex determination", "sex-linked",
      "x-linked", "y-linked", "barr body", "lyon hypothesis", "sex determination.*twin",
      "twins.*boy.*girl", "boy.*girl.*twin",
      "chromosome theory", "morgan", "drosophila"]),

    ("Principles of Inheritance", "Biology", "Mutation and Variations",
     ["mutation", "mutagenic", "mutagen", "point mutation",
      "frame shift", "chromosomal aberration", "aneuploidy",
      "polyploidy", "deletion", "duplication.*chromosome",
      "inversion", "translocation.*chromosome", "down syndrome",
      "turner", "klinefelter", "pedigree", "haemophilia",
      "colour blindness.*genetics"]),

    ("Evolution", "Biology", "Natural Selection",
     ["natural selection", "darwin", "survival of fittest",
      "adaptation", "fitness", "artificial selection",
      "directional selection", "stabilizing selection",
      "disruptive selection", "struggle for existence"]),

    ("Evolution", "Biology", "Origin and Evidence",
     ["origin of life", "oparin", "haldane", "urey miller",
      "chemical evolution", "fossil", "geological", "homologous",
      "analogous", "vestigial", "biogeography",
      "comparative anatomy", "molecular phylogeny"]),

    ("Evolution", "Biology", "Speciation and Hardy Weinberg",
     ["speciation", "allopatric", "sympatric", "reproductive isolation",
      "gene flow", "genetic drift", "founder effect", "bottleneck",
      "hardy.weinberg", "allele frequency", "microevolution",
      "macroevolution",
      "convergent evolution", "divergent evolution",
      "sweet potato.*potato", "potato.*sweet potato"]),

    ("Human Health and Disease", "Biology", "Pathogens and Immunity",
     ["immunity", "innate immunity", "acquired immunity",
      "humoral", "cell-mediated", "antibody", "antigen",
      "b lymphocyte", "t lymphocyte", "memory cell",
      "active immunity", "passive immunity", "vaccination",
      "lymphocyte.*immune"]),

    ("Human Health and Disease", "Biology", "Diseases",
     ["malaria", "typhoid", "amoebiasis", "ascariasis",
      "filariasis", "ringworm", "cold.*common", "pneumonia",
      "aids", "hiv", "cancer", "tumour", "benign", "malignant",
      "metastasis", "carcinogen", "oncogene", "neoplast", "proliferating cell"]),

    ("Biotechnology", "Biology", "Recombinant DNA Technology",
     ["recombinant dna", "restriction enzyme", "restriction endonuclease",
      "ligase", "cloning vector", "plasmid", "bacteriophage",
      "gene cloning", "pcr", "gel electrophoresis",
      "transformation", "transfection", "palindromic",
      "blunt end", "sticky end"]),

    ("Biotechnology", "Biology", "Applications of Biotechnology",
     ["transgenic", "gmo", "golden rice", "bt cotton", "bt toxin",
      "cry protein", "gene therapy", "rnai", "e.*coli.*insulin", "human insulin.*bacteria", "antisense",
      "insulin.*recombinant", "human growth hormone.*biotech",
      "bioreactor", "downstream processing",
      "blue-white selection", "selectable marker",
      "eli lilly", "foam.brak", "foam break", "agitator.*bioreactor", "sparger", "impeller"]),

    ("Ecology", "Biology", "Ecosystem",
     ["ecosystem", "food chain", "food web", "trophic level",
      "energy flow", "productivity", "gpp", "npp",
      "decomposition", "nutrient cycling", "carbon cycle",
      "nitrogen cycle", "phosphorus cycle", "detritus",
      "detritivore", "standing crop"]),

    ("Ecology", "Biology", "Biomes and Succession",
     ["biome", "succession", "father of ecology", "ramdeo misra", "primary succession", "secondary succession",
      "climax community", "pioneer species", "sere", "xerosere",
      "hydrosere", "lithosere", "hygrosere"]),

    ("Ecology", "Biology", "Population Ecology",
     ["population", "natality", "mortality", "age structure",
      "population growth", "logistic growth", "exponential growth",
      "carrying capacity", "r-selected", "k-selected",
      "verhulst", "pearl", "intraspecific", "interspecific",
      "competition", "predation", "parasitism", "mutualism",
      "commensalism", "amensalism", "predator.*prey"]),

    ("Biodiversity and Conservation", "Biology", "Conservation",
     ["biodiversity", "hotspot", "endemic", "endangered",
      "extinct", "conservation", "in-situ", "ex-situ",
      "national park", "wildlife sanctuary", "biosphere reserve",
      "sacred grove", "red data book", "iucn"]),

    ("Plant Physiology", "Biology", "Photosynthesis",
     ["photosynthesis", "light reaction", "dark reaction",
      "calvin cycle", "c3", "c4", "cam", "rubisco", "pgal",
      "photosystem", "z-scheme", "non-cyclic", "cyclic",
      "chemiosmosis.*plant", "chlorophyll", "carotenoid",
      "reaction centre", "antenna molecule", "photorespiration"]),

    ("Plant Physiology", "Biology", "Respiration in Plants",
     ["glycolysis", "krebs cycle", "tca cycle",
      "oxidative phosphorylation", "fermentation",
      "electron transport chain.*plant", "substrate level phosphorylation",
      "respiratory quotient", "rq", "anaerobic respiration",
      "aerobic respiration", "pyruvate"]),

    ("Plant Physiology", "Biology", "Transport and Mineral Nutrition",
     ["transpiration", "stomata", "guard cell", "water potential",
      "osmosis", "plasmolysis", "imbibition", "active transport.*plant",
      "apoplast", "symplast", "cohesion tension", "translocation.*phloem",
      "source.*sink", "mineral nutrition", "essential element",
      "macro.*micronutrient", "nitrogen fixation", "nitrification",
      "denitrification", "rhizobium", "azotobacter", "oscillatoria", "anabaena",
      "cannot fix nitrogen", "nitrogen.*fix"]),

    ("Plant Physiology", "Biology", "Plant Growth Regulators",
     ["auxin", "gibberellin", "cytokinin", "abscisic acid",
      "ethylene", "plant hormone", "apical dominance",
      "bolting", "vernalization", "photoperiodism",
      "short day plant", "long day plant", "day neutral",
      "phytochrome", "senescence.*plant"]),

    ("Cell Biology", "Biology", "Cell Organelles",
     ["mitochondria", "chloroplast", "endoplasmic reticulum",
      "golgi", "ribosome", "lysosome", "peroxisome",
      "vacuole", "centriole", "cell wall", "plasma membrane",
      "nucleus.*cell", "nucleolus", "nuclear pore"]),

    ("Cell Biology", "Biology", "Cell Cycle and Division",
     ["mitosis", "meiosis", "cell cycle", "interphase",
      "prophase", "metaphase", "anaphase", "telophase",
      "synapsis", "bivalent", "tetrad", "chiasma",
      "spindle fiber", "centromere", "kinetochore",
      "cytokinesis", "g1", "s phase", "g2", "m phase"]),

    ("Cell Biology", "Biology", "Membrane and Transport",
     ["fluid mosaic", "semi-permeable", "diffusion",
      "facilitated diffusion", "active transport",
      "endocytosis", "exocytosis", "phagocytosis",
      "pinocytosis", "membrane protein", "receptor protein"]),

    ("Biomolecules (Biology)", "Biology", "Macromolecules",
     ["macromolecule", "polysaccharide.*biology",
      "protein structure", "denaturation.*protein",
      "nucleic acid.*biology", "enzyme.*biology",
      "km.*enzyme", "vmax", "inhibitor.*enzyme",
      "competitive inhibition", "feedback inhibition",
      "coenzyme.*biology", "prosthetic group"]),

    ("Sexual Reproduction in Flowering Plants", "Biology", "Flower and Seed",
     ["pollination", "pollen", "anther", "stigma", "style",
      "double fertilization", "endosperm", "embryo.*plant",
      "ovule", "seed", "fruit", "testa", "cotyledon",
      "germination", "viviparous"]),

    ("Sexual Reproduction in Flowering Plants", "Biology", "Apomixis and Polyembryony",
     ["apomixis", "parthenocarpy", "polyembryony",
      "self-incompatibility", "emasculation"]),

    ("Human Reproduction", "Biology", "Gametogenesis",
     ["spermatogenesis", "oogenesis", "sertoli", "leydig",
      "follicle", "graafian follicle", "corpus luteum",
      "acrosome", "sperm", "ovum", "oocyte",
      "primary spermatocyte", "secondary spermatocyte"]),

    ("Human Reproduction", "Biology", "Fertilization and Development",
     ["fertilization.*human", "implantation", "blastocyst",
      "gastrulation", "placenta", "umbilical cord",
      "amniotic", "embryo.*human", "foetus", "parturition",
      "gestation", "chorion", "hcg", "menarche", "first menstruation"]),

    ("Reproductive Health", "Biology", "Contraception and MTP",
     ["contraceptive", "mtp", "amniocentesis", "stds",
      "sexually transmitted", "iud", "oral pill",
      "condom", "tubectomy", "vasectomy", "reproductive health"]),

    ("Plant Diversity", "Biology", "Algae, Fungi and Lower Plants",
     ["algae", "fungi", "mycorrhiza", "lichen", "bryophyte",
      "liverwort", "moss", "pteridophyte", "fern", "horsetail",
      "thallus", "gametophyte.*plant", "sporophyte.*plant",
      "alternation of generation"]),

    ("Plant Diversity", "Biology", "Gymnosperms and Angiosperms",
     ["gymnosperm", "cycas", "pinus", "angiosperm",
      "monocot", "dicot", "class.*plant", "division.*plant"]),

    ("Animal Diversity", "Biology", "Non-Chordates",
     ["porifera", "coelenterate", "cnidaria", "platyhelminthes",
      "nematoda", "annelida", "arthropoda", "mollusca",
      "echinodermata", "sponge", "hydra", "earthworm",
      "cockroach", "prawn", "starfish", "nematode", "leech"]),

    ("Animal Diversity", "Biology", "Chordates and Vertebrates",
     ["chordate", "vertebrate", "notochord", "cyclostomata",
      "chondrichthyes", "osteichthyes", "amphibia", "reptilia",
      "aves", "mammalia", "shark", "frog", "lizard", "snake",
      "bird.*class", "mammal.*class"]),

    ("Morphology of Flowering Plants", "Biology", "Root and Stem Morphology",
     ["taproot", "fibrous root", "adventitious root",
      "modification.*root", "herbaceous stem", "woody stem",
      "modification.*stem", "runner", "stolon", "tendril.*stem",
      "thorn.*stem", "corm", "bulb", "rhizome"]),

    ("Morphology of Flowering Plants", "Biology", "Leaf and Inflorescence",
     ["leaf", "leaflet", "pinnate", "palmate", "lamina",
      "petiole", "stipule", "leaf modification", "tendril.*leaf",
      "phyllode", "inflorescence", "racemose", "cymose", "zygomorphic", "actinomorphic",
      "spike", "catkin", "head", "umbel", "corymb",
      "flower.*parts", "sepal", "petal", "stamen", "carpel"]),

    ("Anatomy of Flowering Plants", "Biology", "Tissue System",
     ["epidermal tissue", "ground tissue", "vascular tissue",
      "xylem", "phloem", "tracheary", "vessel", "tracheid",
      "sieve tube", "companion cell", "collenchyma",
      "sclerenchyma", "parenchyma", "meristem",
      "apical meristem", "lateral meristem", "intercalary"]),

    ("Anatomy of Flowering Plants", "Biology", "Root, Stem, Leaf Anatomy",
     ["root anatomy", "cortex", "pith", "endodermis",
      "casparian strip", "pericycle", "conjoint vascular",
      "collateral vascular", "stem anatomy",
      "monocot root", "dicot root", "monocot stem", "dicot stem",
      "leaf anatomy", "mesophyll", "palisade", "spongy"]),

    ("Structural Organisation in Animals", "Biology", "Animal Tissues",
     ["epithelial tissue", "connective tissue", "muscle tissue",
      "nervous tissue", "squamous", "cuboidal", "columnar",
      "stratified", "glandular epithelium", "ciliated",
      "areolar tissue", "adipose", "blood.*tissue",
      "cartilage", "bone tissue"]),

    ("Structural Organisation in Animals", "Biology", "Cockroach and Frog",
     ["cockroach", "frog.*anatomy", "alimentary canal.*frog",
      "digestive system.*frog", "nervous system.*cockroach",
      "reproductive system.*cockroach", "malpighian tubule"]),

    ("Digestion and Absorption", "Biology", "GI Tract",
     ["digestion", "absorption", "peristalsis", "gastric juice",
      "pepsin", "trypsin", "chymotrypsin", "lipase",
      "amylase", "bile", "bile salt", "liver", "pancreas",
      "villus", "microvilli", "absorption.*intestine",
      "portal vein", "small intestine", "large intestine",
      "stomach", "oesophagus", "duodenum"]),

    ("Breathing and Exchange of Gases", "Biology", "Respiratory System",
     ["lung", "alveolus", "alveolar", "breathing",
      "respiratory", "tidal volume", "vital capacity",
      "inspiratory", "expiratory", "residual volume",
      "emphysema", "asthma", "pleura", "diaphragm",
      "haemoglobin.*oxygen", "oxygen dissociation",
      "bohr effect", "co2 transport", "carbaminohaemoglobin",
      "bicarbonate.*blood"]),

    ("Body Fluids and Circulation", "Biology", "Heart and Blood",
     ["cardiac", "heart", "atrium", "ventricle", "sino-atrial",
      "av node", "bundle of his", "purkinje", "ecg",
      "systole", "diastole", "blood pressure",
      "coronary", "portal circulation",
      "blood group", "abo", "rh factor"]),

    ("Body Fluids and Circulation", "Biology", "Blood Components",
     ["plasma", "erythrocyte", "leucocyte", "platelet",
      "haemoglobin", "rbc", "wbc", "lymph", "serum",
      "clotting", "prothrombin", "fibrinogen", "thrombin",
      "fibrin", "erythropoietin"]),

    ("Excretory Products and their Elimination", "Biology", "Kidney and Urine Formation",
     ["kidney", "nephron", "glomerulus", "bowman", "proximal tubule",
      "distal tubule", "loop of henle", "collecting duct",
      "ultrafiltration", "reabsorption", "secretion.*tubular",
      "urea", "creatinine", "uric acid", "gfr",
      "juxtaglomerular", "renin", "angiotensin", "aldosterone"]),

    ("Locomotion and Movement", "Biology", "Muscle Contraction",
     ["muscle", "sarcomere", "myosin", "actin", "troponin",
      "tropomyosin", "sliding filament", "neuromuscular junction",
      "acetylcholine.*muscle", "atp.*muscle contraction",
      "tetanus.*muscle", "rigor mortis"]),

    ("Locomotion and Movement", "Biology", "Skeleton",
     ["bone", "cartilage.*skeleton", "joint", "synovial",
      "axial skeleton", "appendicular skeleton",
      "pectoral girdle", "pelvic girdle",
      "ossification", "osteoblast", "osteoclast"]),

    ("Neural Control and Coordination", "Biology", "Nervous System",
     ["neuron", "synapse", "action potential", "resting potential",
      "membrane potential", "depolarization", "repolarization",
      "axon", "dendrite", "myelin", "schwann", "saltatory",
      "central nervous system", "peripheral nervous",
      "brain", "cerebrum", "cerebellum", "medulla",
      "spinal cord", "reflex arc", "reflex action",
      "autonomic", "sympathetic", "parasympathetic"]),

    ("Neural Control and Coordination", "Biology", "Sensory Organs",
     ["eye", "ear", "cochlea", "organ of corti",
      "retina", "rod", "cone", "photoreceptor",
      "lens.*eye", "aqueous humour", "vitreous humour",
      "cornea", "iris", "pupil", "sclera",
      "eustachian tube", "tympanic membrane",
      "semicircular canal", "vestibule.*ear",
      "taste", "smell", "olfactory"]),

    ("Chemical Coordination and Integration", "Biology", "Endocrine System",
     ["hormone", "endocrine", "pituitary", "hypothalamus",
      "thyroid", "parathyroid", "adrenal", "pancreas.*hormone",
      "insulin.*biology", "glucagon", "gonadotropin",
      "testosterone", "estrogen", "progesterone",
      "growth hormone", "tsh", "acth", "fsh", "lh",
      "oxytocin", "vasopressin", "adrenaline", "cortisol",
      "melatonin", "prostaglandin", "insulin.*oral", "oral.*insulin",
      "diabetic.*oral", "reductionist biology"]),

    ("Strategies for Enhancement in Food Production", "Biology", "Plant and Animal Breeding",
     ["plant breeding", "animal breeding", "hybridization.*breeding",
      "selection.*breeding", "mutation breeding",
      "polyploidy.*breeding", "tissue culture",
      "somaclonal variation", "somatic hybridization",
      "protoplast fusion", "green revolution",
      "semi-dwarf", "high yielding variety",
      "heterosis", "inbreeding.*animal"]),

    ("Strategies for Enhancement in Food Production", "Biology", "Biofortification",
     ["biofortification", "golden rice", "protein quality",
      "single cell protein", "spirulina", "mushroom cultivation",
      "pisciculture", "aquaculture", "apiculture",
      "poultry", "animal husbandry"]),

    ("Microbes in Human Welfare", "Biology", "Microbes",
     ["biogas", "gobar gas", "biogas plant", "sewage treatment",
      "bod.*biology", "activated sludge", "antibiotics",
      "penicillin", "streptomycin", "fermentation.*biology",
      "yeast.*biology", "lactobacillus", "aspergillus",
      "trichoderma", "mycorrhiza.*welfare", "biopesticide",
      "biofertilizer", "rhizobium.*nitrogen"]),
]

# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────────

def score_question(text: str) -> dict[str, int]:
    """Return {topic_label: score} for all topics that matched at least 1 keyword."""
    scores: dict[str, int] = defaultdict(int)
    for (topic, subject, subtopic, keywords) in RULES:
        label = f"{topic}|||{subject}|||{subtopic}"
        for kw in keywords:
            if re.search(kw, text, re.IGNORECASE):
                scores[label] += 1
    return scores


def assign_topic(q: dict) -> tuple[str, str]:
    """Return (topic, subtopic) for a question dict."""
    full_text = q["text"] + " " + " ".join(q["options"])
    scores = score_question(full_text)

    if not scores:
        # Fallback: subject-level coarse assignment only
        subj = q["subject"]
        return f"General {subj}", subj

    # Among rules in the same subject, pick highest score
    subj = q["subject"]
    best_label = max(
        (lbl for lbl in scores if lbl.split("|||")[1] == subj),
        key=lambda lbl: scores[lbl],
        default=None,
    )
    if best_label is None:
        return f"General {subj}", subj

    topic, _, subtopic = best_label.split("|||")
    return topic, subtopic


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    questions: list[dict] = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))

    # Build topics.json: {str(year): {topic: [q_numbers]}}
    topics: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))

    for q in questions:
        topic, subtopic = assign_topic(q)
        q["topic"]    = topic
        q["subtopic"] = subtopic
        year_key = str(q["year"])
        topics[year_key][topic].append(q["q_number"])

    # Write topics.json  (sort q_numbers and topics)
    topics_out: dict[str, dict[str, list[int]]] = {}
    for yr in sorted(topics):
        topics_out[yr] = {t: sorted(v) for t, v in sorted(topics[yr].items())}

    TOPICS_JSON.write_text(
        json.dumps(topics_out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote {TOPICS_JSON}")

    # Write enriched questions.json
    QUESTIONS_JSON.write_text(
        json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Updated {QUESTIONS_JSON}")

    # ── Summary ──
    print("\n=== 2025 Topic Distribution ===")
    for topic, q_nums in sorted(topics_out.get("2025", {}).items()):
        print(f"  {topic:<50} {len(q_nums):>3} qs  {q_nums}")

    # Coverage stats
    fallback_topics = {"General Physics", "General Chemistry", "General Biology"}
    unclassified = [q for q in questions if q["topic"] in fallback_topics]
    print(f"\nUnclassified (General fallback): {len(unclassified)}")
    for q in unclassified:
        print(f"  Q{q['q_number']} [{q['subject']}]: {q['text'][:80]}")


if __name__ == "__main__":
    main()
