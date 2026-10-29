# ============================================================
# ALZHEIMER MRI STAGING - MEDICAL AI CHATBOT SERVICE
# ============================================================

import os
import re
import time
from typing import Dict, Any, List, Optional
import httpx

# Reputable evidence sources
DEFAULT_SOURCES = [
    {"name": "National Institute on Aging (NIA)", "url": "https://www.nia.nih.gov/health/alzheimers-and-dementia"},
    {"name": "Alzheimer's Association", "url": "https://www.alz.org"},
    {"name": "World Health Organization (WHO) Dementia Guidelines", "url": "https://www.who.int/news-room/fact-sheets/detail/dementia"},
    {"name": "Lancet Commission on Dementia Prevention", "url": "https://www.thelancet.com"}
]

SYSTEM_PROMPT = """You are NEUROSTAGE AI Medical Assistant, an educational medical information assistant specializing in Alzheimer's disease, dementia, cognitive health, and structural MRI research staging.

CORE PRINCIPLES & CLINICAL SAFETY:
1. You are NOT a doctor. You provide educational medical information and research context only.
2. NEVER diagnose a patient, confirm Alzheimer's disease, or rule out dementia.
3. NEVER prescribe medications, recommend dosages, or advise stopping or changing prescribed medications.
4. Clearly state that a clinical diagnosis requires comprehensive evaluation by a qualified physician (neurologist or geriatrician) including clinical history, physical and neurological examinations, cognitive tests (like MMSE/MoCA), lab work, and appropriate neuroimaging.
5. Emphasize that structural MRI alone does not provide a definitive diagnosis of Alzheimer's disease.
6. When explaining the website's AI MRI report: explain only the structured metrics provided (model name, predicted stage, confidence, Monte Carlo uncertainty, slice count, probability aggregation). Explicitly remind the user that this is an AI research prototype and not a clinical diagnosis. NEVER fabricate radiological findings (such as hippocampal atrophy or brain volume loss) if they are not explicitly measured by the model.
7. For acute emergencies or sudden neurological signs (sudden weakness, facial drooping, difficulty speaking, severe confusion, seizure, sudden loss of consciousness, severe thunderclap headache, vision loss): Immediately recommend urgent medical care without a lengthy Alzheimer's discussion. For India/general users: "If this is happening now, seek emergency medical care immediately or call your local emergency service."
8. Structure answers clearly when explaining medical concepts:
   - Short Answer: Clear, concise summary.
   - What It Means / Why: Scientific reasoning and evidence-based justification.
   - What You Can Do: Practical, non-prescriptive lifestyle or general guidance.
   - When to See a Doctor: Specific clinical indicators for professional consultation.
   - Sources: Cite reputable medical organizations (NIA, Alzheimer's Association, WHO).
"""

EMERGENCY_KEYWORDS = [
    r"\bsudden\s+weakness\b",
    r"\bfacial\s+droop\w*\b",
    r"\bsudden\s+(trouble|difficulty)\s+speaking\b",
    r"\bslurred\s+speech\b",
    r"\bseizure\b",
    r"\bloss\s+of\s+consciousness\b",
    r"\bpassed\s+out\b",
    r"\bunconscious\b",
    r"\bsudden\s+severe\s+headache\b",
    r"\bthunderclap\s+headache\b",
    r"\bsudden\s+vision\s+loss\b",
    r"\bsudden\s+confusion\b",
    r"\bchest\s+pain\b",
    r"\bstroke\b",
    r"\bheart\s+attack\b"
]


class MedicalChatProvider:
    """
    Provider abstraction for NEUROSTAGE AI Medical Assistant.
    Supports OpenAI, Groq, Google Gemini LLMs with smart circuit breakers,
    and a comprehensive evidence-based clinical knowledge engine covering over 28 medical & technical categories.
    """

    def __init__(self):
        # Load from .env files if present
        from pathlib import Path
        for p in [Path("backend/.env"), Path(".env")]:
            if p.exists():
                try:
                    for line in p.read_text().splitlines():
                        if "=" in line and not line.strip().startswith("#"):
                            k, v = line.split("=", 1)
                            os.environ[k.strip()] = v.strip()
                except Exception:
                    pass

        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        
        # Accept GEMINI_API_KEY or GOOGLE_API_KEY only if it matches standard AI Studio format
        gemini_candidate = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if gemini_candidate and (gemini_candidate.startswith("AIzaSy") or os.getenv("GEMINI_API_KEY")):
            self.gemini_key = gemini_candidate
        else:
            self.gemini_key = None

        # Provider circuit breakers (avoid repeat 429/401 latency)
        self._openai_disabled_until = 0.0
        self._groq_disabled_until = 0.0
        self._gemini_disabled_until = 0.0

    def _check_emergency(self, message: str) -> Optional[Dict[str, Any]]:
        """Identify acute emergency or stroke signs and return immediate guidance."""
        lower = message.lower()
        for pattern in EMERGENCY_KEYWORDS:
            if re.search(pattern, lower):
                return {
                    "answer": (
                        "⚠️ **URGENT MEDICAL NOTICE**\n\n"
                        "The symptoms you described (such as sudden weakness, facial drooping, slurred speech, "
                        "seizure, loss of consciousness, sudden severe headache, or acute confusion) can be signs "
                        "of a life-threatening medical emergency, such as an acute stroke or neurological catastrophe.\n\n"
                        "**Immediate Action Required:**\n"
                        "- **If this is happening now, call emergency medical services immediately (such as 112 in India, 911 in the US, or 999 in the UK) or go to the nearest emergency room.**\n"
                        "- Remember the **FAST** signs for stroke:\n"
                        "  - **F**ace: Is one side of the face drooping?\n"
                        "  - **A**rms: Can the person raise both arms, or does one drift downward?\n"
                        "  - **S**peech: Is speech slurred or strange?\n"
                        "  - **T**ime: Time to call emergency services immediately.\n"
                        "- Do not wait to see if symptoms improve, and do not drive yourself.\n\n"
                        "*NEUROSTAGE AI cannot evaluate or manage acute medical emergencies.*"
                    ),
                    "sources": [
                        {"name": "American Stroke Association (FAST signs)", "url": "https://www.stroke.org"},
                        {"name": "World Health Organization Emergency Care", "url": "https://www.who.int"}
                    ],
                    "category": "emergency_alert",
                    "disclaimer": "Emergency symptoms require immediate emergency department care."
                }
        return None

    def _format_mri_context_prompt(self, mri_context: Dict[str, Any]) -> str:
        """Format user's current session MRI prediction context for the assistant."""
        if not mri_context:
            return ""

        pred = mri_context.get("prediction", {})
        vol_meta = mri_context.get("volume_metadata", {})

        model_name = mri_context.get("model_name") or pred.get("model_name", "AI Model")
        stage = pred.get("class_name", "Unknown")
        conf = pred.get("confidence", 0) * 100
        uncertainty = pred.get("uncertainty", 0)
        probs = pred.get("probabilities", {})
        slices = vol_meta.get("valid_slices_extracted") or mri_context.get("num_slices", "N/A")

        prob_str = ", ".join([f"{k}: {v*100:.1f}%" for k, v in probs.items()]) if probs else "N/A"

        return (
            f"\n[CURRENT USER MRI PREDICTION SESSION DATA]\n"
            f"- Model Used: {model_name}\n"
            f"- AI Predicted Stage: {stage}\n"
            f"- Staging Confidence: {conf:.1f}%\n"
            f"- Monte Carlo Dropout Uncertainty (Entropy): {uncertainty:.3f}\n"
            f"- Class Probability Distribution: {prob_str}\n"
            f"- Informative Axial Slices Analyzed: {slices}\n"
            f"- Aggregation Strategy: Patient-level mean probability aggregation\n"
            f"- Research Status: Research prototype (Zero patient data leakage, OASIS-1 trained)\n"
            f"[END OF MRI CONTEXT]\n"
        )

    def _build_knowledge_base_response(self, message: str, mri_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extensive evidence-based clinical knowledge engine.
        Answers user questions across 28+ categories with clear structure, scientific justification,
        practical recommendations, and reputable clinical citations.
        """
        q = message.lower().strip()

        # -------------------------------------------------------------
        # 1. Greetings / Help / Identity
        # -------------------------------------------------------------
        if any(re.search(rf"\b{w}\b", q) for w in ["hi", "hello", "hey", "greetings", "good morning", "good evening", "good afternoon"]) or \
           any(p in q for p in ["who are you", "what can you do", "what do you do", "help me", "what is your name", "what is neurostage"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Hello! I am the **NEUROSTAGE AI Medical Assistant**, an educational companion specializing in Alzheimer's disease, "
                    "dementia symptoms, brain health, and structural MRI staging.\n\n"
                    "**How I Can Help You:**\n"
                    "- **Explain Alzheimer's & Dementia:** Understand causes, 10 warning signs, stages, and risk factors.\n"
                    "- **Explain Your MRI Analysis:** Break down your AI model predictions, confidence percentages, Monte Carlo uncertainty, and slice aggregation.\n"
                    "- **Diagnostic Pathways:** Explain clinical cognitive tests (MoCA, MMSE), blood biomarkers (p-tau217), and imaging findings.\n"
                    "- **Lifestyle & Prevention:** Evidence-based guidance on diet (MIND/Mediterranean), exercise, sleep, and cardiovascular care.\n"
                    "- **Caregiver Guidance:** Practical strategies for supporting loved ones with memory loss.\n\n"
                    "**Important Medical Boundary:**\n"
                    "I provide medical education and research explanations. I do not diagnose conditions, prescribe medications, or replace a doctor's examination."
                ),
                "sources": DEFAULT_SOURCES[:2],
                "category": "assistant_introduction",
                "disclaimer": "Educational medical information — not a clinical diagnosis."
            }

        # -------------------------------------------------------------
        # 2. Diagnosis Requests / "Do I have Alzheimer's?"
        # -------------------------------------------------------------
        if any(p in q for p in ["do i have", "diagnose me", "am i sick", "have i got", "tell me if i have", "do you think i have", "can you check if i have", "test me"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "I cannot diagnose you, and this AI tool cannot determine whether you have Alzheimer's disease.\n\n"
                    "**What It Means:**\n"
                    "A clinical diagnosis of Alzheimer's disease cannot be made by an online AI tool or an MRI scan alone. "
                    "Memory changes can stem from numerous conditions—many of which are treatable or reversible (such as vitamin B12 deficiency, "
                    "thyroid imbalances, medication interactions, sleep apnea, depression, or metabolic disturbances).\n\n"
                    "**How Alzheimer's Is Clinically Diagnosed:**\n"
                    "1. **Clinical History:** Detailed interviews regarding daily functioning, memory changes, and family background.\n"
                    "2. **Cognitive Testing:** Standardized assessments such as the Montreal Cognitive Assessment (MoCA) or Mini-Mental State Examination (MMSE).\n"
                    "3. **Laboratory Blood Panels:** Complete metabolic panel, TSH, vitamin B12, and emerging plasma biomarkers (such as p-tau217).\n"
                    "4. **Neuroimaging:** Diagnostic structural MRI evaluated by certified radiologists to assess patterns of brain atrophy and rule out strokes or lesions.\n\n"
                    "**When to See a Doctor:**\n"
                    "If you or a loved one are experiencing persistent memory lapses that interfere with daily activities (like repeating questions, "
                    "getting lost in familiar places, or having trouble managing finances), consult a primary care physician or neurologist for an in-person evaluation."
                ),
                "sources": [
                    {"name": "National Institute on Aging: How Is Alzheimer's Diagnosed?", "url": "https://www.nia.nih.gov/health/alzheimers-and-dementia"},
                    {"name": "Alzheimer's Association Diagnostic Guidelines", "url": "https://www.alz.org/alzheimers-dementia/diagnosis"}
                ],
                "category": "diagnosis_inquiry",
                "disclaimer": "Educational information only — not a clinical diagnosis."
            }

        # -------------------------------------------------------------
        # 3. Medications & Specific Drugs
        # -------------------------------------------------------------
        specific_drugs = ["donepezil", "aricept", "memantine", "namenda", "lecanemab", "leqembi", "donanemab", "kisunla", "rivastigmine", "exelon", "galantamine", "razadyne", "aducanumab", "aduhelm"]
        matched_drug = next((d for d in specific_drugs if d in q), None)

        if matched_drug:
            drug_cap = matched_drug.capitalize()
            return {
                "answer": (
                    f"**Short Answer:**\n"
                    f"**{drug_cap}** is an FDA/regulatory approved therapy used in the management of Alzheimer's disease. "
                    f"It must only be prescribed, administered, and monitored by a qualified healthcare professional.\n\n"
                    f"**What It Is & How It Works:**\n"
                    f"- **Cholinesterase Inhibitors (Donepezil, Rivastigmine, Galantamine):** Prevent the breakdown of acetylcholine, a neurotransmitter critical for memory and learning, helping manage symptoms in mild to moderate stages.\n"
                    f"- **NMDA Receptor Antagonists (Memantine):** Regulate glutamate activity to protect brain cells from excess calcium toxicity in moderate to severe Alzheimer's.\n"
                    f"- **Disease-Modifying Monoclonal Antibodies (Lecanemab / Leqembi, Donanemab / Kisunla):** Target and remove amyloid-beta plaques in early-stage Alzheimer's / MCI. They require strict eligibility, ApoE gene testing, and routine MRI monitoring for Amyloid-Related Imaging Abnormalities (ARIA/brain edema).\n\n"
                    f"**Important Safety Note:**\n"
                    f"Do not start, stop, or alter medication dosages without explicit guidance from your treating physician. Discuss potential side effects and interactions directly with your neurologist."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Alzheimer's Medications", "url": "https://www.nia.nih.gov/health/alzheimers-medicines"},
                    {"name": "Alzheimer's Association Approved Treatments", "url": "https://www.alz.org/alzheimers-dementia/treatments"}
                ],
                "category": "medication_guidance",
                "disclaimer": "Educational overview of treatments — does not constitute medical prescription."
            }

        if any(w in q for w in ["medicine", "medication", "drug", "prescribe", "prescription", "dose", "dosage", "pill", "pills"]) or \
           ("treatment" in q and not any(w in q for w in ["cure", "prevent", "lifestyle"])):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "I cannot prescribe medications or recommend specific dosages. All therapeutic decisions must be made directly with a licensed physician.\n\n"
                    "**Overview of Approved Alzheimer's Treatments:**\n"
                    "1. **Symptom-Managing Therapies:**\n"
                    "   - *Cholinesterase Inhibitors* (Donepezil, Rivastigmine, Galantamine): Support acetylcholine signaling to temporarily stabilize memory and cognition in mild to moderate disease.\n"
                    "   - *NMDA Receptor Antagonist* (Memantine): Protects nerve cells against excessive glutamate excitation, often prescribed in moderate to severe stages.\n"
                    "2. **Disease-Modifying Biologics:**\n"
                    "   - *Anti-Amyloid Monoclonal Antibodies* (Lecanemab/Leqembi, Donanemab/Kisunla): Help clear amyloid plaques in early symptomatic stages (MCI or mild dementia), slowing clinical decline by ~27–35% in clinical trials.\n"
                    "   - These therapies require regular MRI monitoring to watch for ARIA (brain swelling or microbleeds).\n\n"
                    "**What You Can Do:**\n"
                    "Consult a neurologist or geriatrician to discuss whether these therapies are medically indicated based on the individual's stage, medical history, and risk factors."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Alzheimer's Treatments", "url": "https://www.nia.nih.gov/health/alzheimers-medicines"},
                    {"name": "Alzheimer's Association Treatment Overview", "url": "https://www.alz.org/alzheimers-dementia/treatments"}
                ],
                "category": "medication_guidance",
                "disclaimer": "Educational overview of treatments — does not constitute medical prescription."
            }

        # -------------------------------------------------------------
        # 4. User's AI MRI Result & Current Session Scan Explanation
        # -------------------------------------------------------------
        if (("my" in q or "explain" in q or "this" in q) and any(w in q for w in ["result", "scan", "report", "staging", "prediction"])) or \
           any(p in q for p in ["why did the ai predict", "confidence mean", "uncertainty mean", "my diagnosis"]):
            if mri_context and "prediction" in mri_context:
                pred = mri_context["prediction"]
                stage = pred.get("class_name", "Unknown")
                conf = pred.get("confidence", 0) * 100
                unc = pred.get("uncertainty", 0)
                model_used = pred.get("model_name", "Selected AI Model")
                probs = pred.get("probabilities", {})

                prob_details = "\n".join([f"- **{k}**: {v*100:.1f}%" for k, v in probs.items()]) if probs else ""

                return {
                    "answer": (
                        f"**Explanation of Your Current AI MRI Analysis:**\n\n"
                        f"- **Model Used:** {model_used}\n"
                        f"- **AI Predicted Staging:** **{stage}**\n"
                        f"- **Prediction Confidence:** **{conf:.1f}%**\n"
                        f"- **Monte Carlo Uncertainty (Predictive Entropy):** **{unc:.3f}**\n\n"
                        f"**Full Class Probability Breakdown:**\n{prob_details}\n\n"
                        f"**What It Means Scientifically:**\n"
                        f"1. **Slice Extraction & Aggregation:** The AI examined informative 2D axial slices throughout the 3D MRI volume, extracted deep feature maps, and pooled individual slice predictions using mean probability pooling.\n"
                        f"2. **Uncertainty Interpretation ({unc:.3f}):** Computed via stochastic Monte Carlo Dropout passes. Lower values indicate strong mathematical consensus across dropout iterations, while higher values signify ambiguity in feature representations.\n"
                        f"3. **Research Prototype Nature:** The model was trained on the OASIS-1 research benchmark. It is designed to evaluate algorithmic staging capabilities, not to serve as an official radiology report.\n\n"
                        f"**Clinical Next Steps:**\n"
                        f"If you have clinical concerns or symptoms, provide the original diagnostic MRI study (DICOM format) to a licensed neuroradiologist and neurologist for standard medical interpretation."
                    ),
                    "sources": DEFAULT_SOURCES[:2],
                    "category": "report_explanation",
                    "disclaimer": "Research prototype analysis — not a clinical radiology or medical diagnosis."
                }
            else:
                return {
                    "answer": (
                        "**Short Answer:**\n"
                        "I don't see an MRI analysis result loaded for your current session yet. You can upload a 3D structural MRI file (.nii or .nii.gz) in the **MRI Analysis** tab.\n\n"
                        "**What the AI System Evaluates:**\n"
                        "- **Informative Axial Slices:** Slices containing brain tissue are preprocessed, intensity-normalized, and passed through a convolutional backbone.\n"
                        "- **Patient-Level Aggregation:** Individual slice probabilities are pooled using mean probability aggregation across the full volume.\n"
                        "- **Uncertainty Estimation:** Monte Carlo Dropout produces predictive entropy to reflect model confidence.\n\n"
                        "Once you upload and run an MRI scan, click **'Ask AI Assistant About This Result'** and I will break down your specific staging numbers!"
                    ),
                    "sources": DEFAULT_SOURCES[:2],
                    "category": "report_explanation",
                    "disclaimer": "Educational information on AI pipeline."
                }

        # -------------------------------------------------------------
        # 5. Dementia vs. Alzheimer's (Evaluated before general definition)
        # -------------------------------------------------------------
        if ("dementia" in q and "alzheimer" in q and any(w in q for w in ["diff", "vs", "same", "between", "compare", "relation"])) or \
           any(p in q for p in ["types of dementia", "other dementia", "vascular dementia", "lewy body", "frontotemporal", "ftd"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "**Dementia** is an umbrella term for severe cognitive decline that interferes with everyday life, "
                    "whereas **Alzheimer's disease** is a specific medical disease and the most common cause of dementia (60% to 80% of cases).\n\n"
                    "**The Medical Analogy:**\n"
                    "Think of 'Dementia' as a general symptom category like 'Fever' or 'Heart Disease', "
                    "and 'Alzheimer's Disease' as the specific condition causing it (like a specific infection or coronary artery disease).\n\n"
                    "**Other Major Causes of Dementia:**\n"
                    "- **Vascular Dementia:** Caused by impaired blood supply to the brain (e.g., following strokes or chronic microvascular damage).\n"
                    "- **Lewy Body Dementia:** Characterized by visual hallucinations, fluctuating alertness, and Parkinson-like movement symptoms.\n"
                    "- **Frontotemporal Dementia (FTD):** Marked by prominent changes in personality, social behavior, and language, often starting at a younger age (45–65).\n"
                    "- **Mixed Dementia:** Presence of multiple pathologies simultaneously (most frequently Alzheimer's + vascular changes)."
                ),
                "sources": [
                    {"name": "National Institute on Aging: What Is Dementia?", "url": "https://www.nia.nih.gov/health/what-is-dementia"},
                    {"name": "Alzheimer's Association: Dementia vs. Alzheimer's", "url": "https://www.alz.org"}
                ],
                "category": "dementia_vs_alzheimers",
                "disclaimer": "Educational information."
            }

        # -------------------------------------------------------------
        # 6. What is Alzheimer's Disease? (Definition)
        # -------------------------------------------------------------
        if (any(p in q for p in ["what is alzheimer", "what is alzheimers", "define alzheimer", "explain alzheimer", "about alzheimer", "tell me about alzheimer"]) or \
            (q.startswith("what is") and "alzheimer" in q)) and \
           not any(p in q for p in ["stage", "sign", "symptom", "cause", "prevent", "dementia", "diff", "vs", "between", "genetic", "cure", "test"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "**Alzheimer's disease** is a progressive, neurodegenerative brain disorder and the most common cause of dementia, "
                    "accounting for an estimated 60% to 80% of all dementia cases worldwide.\n\n"
                    "**What Happens in the Brain:**\n"
                    "- **Amyloid-Beta Plaques:** Clusters of protein fragments accumulate between neurons, disrupting communication.\n"
                    "- **Tau Neurofibrillary Tangles:** Twisted fibers of abnormal tau protein build up inside neurons, collapsing transport systems.\n"
                    "- **Neuronal Loss & Atrophy:** As brain cells lose function and die, brain regions responsible for memory (such as the hippocampus) gradually shrink.\n\n"
                    "**How It Typically Manifests:**\n"
                    "It usually starts with subtle memory loss (trouble remembering recent conversations, names, or events) and slowly progresses over years "
                    "to affect language, reasoning, spatial judgment, and independent living.\n\n"
                    "**Sources:**\n"
                    "- National Institute on Aging (NIA): Alzheimer's Basics\n"
                    "- World Health Organization (WHO): Dementia Fact Sheet"
                ),
                "sources": [
                    {"name": "National Institute on Aging (NIA)", "url": "https://www.nia.nih.gov/health/alzheimers-and-dementia"},
                    {"name": "World Health Organization (WHO)", "url": "https://www.who.int/news-room/fact-sheets/detail/dementia"}
                ],
                "category": "disease_definition",
                "disclaimer": "Educational medical information."
            }

        # -------------------------------------------------------------
        # 6. Head Injuries, Concussions, & TBI
        # -------------------------------------------------------------
        if any(w in q for w in ["head injur", "concussion", "concussions", "tbi", "traumatic brain", "cte", "head trauma"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Traumatic Brain Injury (TBI) and repeated head concussions are established risk factors that increase the long-term likelihood "
                    "of developing cognitive impairment, Alzheimer's disease, and Chronic Traumatic Encephalopathy (CTE).\n\n"
                    "**Biological Connection:**\n"
                    "- **Axonal Shearing & Inflammation:** Severe or repeated impacts damage nerve axons and trigger sustained microglial neuroinflammation.\n"
                    "- **Accelerated Protein Aggregation:** Brain trauma has been shown to accelerate the accumulation of both tau protein and amyloid-beta in damaged tissue.\n"
                    "- **CTE vs. Alzheimer's:** While Alzheimer's begins in medial temporal structures (hippocampus), CTE characteristically features tau deposits in the depths of cerebral cortical sulci (often seen in contact sport athletes or blast-exposed veterans).\n\n"
                    "**What You Can Do:**\n"
                    "Protect your brain by wearing helmets, using seatbelts, and seeking prompt medical evaluation following any head injury or loss of consciousness."
                ),
                "sources": [
                    {"name": "National Institute on Aging: TBI and Dementia Risk", "url": "https://www.nia.nih.gov"},
                    {"name": "Alzheimer's Association: Traumatic Brain Injury", "url": "https://www.alz.org"}
                ],
                "category": "tbi_neurotrauma",
                "disclaimer": "Educational information on neurotrauma."
            }

        # -------------------------------------------------------------
        # 7. Causes & Pathophysiology (Amyloid, Tau, Biology)
        # -------------------------------------------------------------
        if (any(w in q for w in ["patholog", "pathophysiology", "amyloid", "tau", "plaque", "tangle", "neurofibrill", "etiology"]) or \
            (any(w in q for w in ["cause", "causes"]) and any(w in q for w in ["alzheimer", "dementia", "disease", "it", "brain", "illness", "condition"])) or \
            ("why" in q and any(w in q for w in ["develop", "happen", "occur", "get alzheimer"]))):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Alzheimer's disease is caused by an intricate combination of age-related brain changes, genetic predispositions, "
                    "environmental factors, and the pathological accumulation of two abnormal proteins: **beta-amyloid** and **tau**.\n\n"
                    "**Biological Mechanisms:**\n"
                    "1. **Beta-Amyloid Plaques:** Amyloid precursor protein (APP) fragments aggregate into toxic oligomers and plaques outside brain cells, causing synaptic dysfunction.\n"
                    "2. **Tau Neurofibrillary Tangles:** In healthy neurons, tau stabilizes internal microtubules. In Alzheimer's, tau becomes hyperphosphorylated, detaches, and forms tangled fibers inside cells, starving them of nutrients.\n"
                    "3. **Neuroinflammation:** The brain's resident immune cells (microglia and astrocytes) fail to clear debris effectively, triggering chronic inflammatory responses that damage surrounding tissue.\n"
                    "4. **Vascular Contributions:** Impaired cerebral blood flow and blood-brain barrier dysfunction exacerbate neurodegeneration.\n\n"
                    "**Key Risk Factors:**\n"
                    "- **Age:** The greatest known risk factor (most individuals diagnosed are 65 or older).\n"
                    "- **Genetics:** APOE-ε4 allele and rare deterministic mutations (APP, PSEN1, PSEN2).\n"
                    "- **Cardiovascular Health:** Hypertension, diabetes, obesity, and physical inactivity."
                ),
                "sources": [
                    {"name": "National Institute on Aging: What Causes Alzheimer's?", "url": "https://www.nia.nih.gov/health/alzheimers-causes-and-risk-factors"},
                    {"name": "Alzheimer's Association: Causes and Risk Factors", "url": "https://www.alz.org"}
                ],
                "category": "pathophysiology",
                "disclaimer": "Educational medical explanation."
            }

        # -------------------------------------------------------------
        # 7. Genetics & Heredity ("Is it genetic?")
        # -------------------------------------------------------------
        if any(w in q for w in ["genetic", "heredit", "inherit", "apoe", "apoe4", "gene", "genes", "dna"]) or \
           (("parent" in q or "mother" in q or "father" in q or "family" in q) and any(w in q for w in ["alzheimer", "dementia", "risk", "have it"])):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Most cases of Alzheimer's disease are **not directly inherited**, but having a parent or sibling with Alzheimer's slightly increases your risk.\n\n"
                    "**Two Forms of Genetic Influence:**\n"
                    "1. **Late-Onset Alzheimer's (Sporadic, >99% of cases):**\n"
                    "   - Develops after age 65.\n"
                    "   - The most significant genetic risk factor is the **APOE-ε4** gene allele.\n"
                    "   - Inheriting one copy of APOE-ε4 increases risk; inheriting two copies increases risk further. However, having APOE-ε4 **does not guarantee** you will develop the disease, and many people without the gene do develop it.\n"
                    "2. **Early-Onset Familial Alzheimer's (<1% of cases):**\n"
                    "   - Typically develops between ages 30 and 60.\n"
                    "   - Caused by deterministic mutations in one of three genes: **APP, PSEN1, or PSEN2**.\n"
                    "   - Individuals who inherit these specific mutations almost certainly develop the disease.\n\n"
                    "**What You Can Do:**\n"
                    "Genetic counseling is recommended before pursuing commercial genetic testing (like ApoE testing), as lifestyle factors (diet, exercise, cardiovascular control) play a crucial role regardless of genetic background."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Alzheimer's Genetics", "url": "https://www.nia.nih.gov/health/alzheimers-disease-genetics-fact-sheet"},
                    {"name": "Alzheimer's Association Genetics", "url": "https://www.alz.org"}
                ],
                "category": "genetics_education",
                "disclaimer": "Genetic risk is not a diagnosis. Consult a genetic counselor for testing questions."
            }

        # -------------------------------------------------------------
        # 8. Cure, Reversal & Recovery ("Can it be cured?")
        # -------------------------------------------------------------
        if any(w in q for w in ["cure", "curable", "reversible", "reverse", "recover", "recovery", "is it fatal", "can you survive", "survivable", "stop alzheimer"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Currently, there is **no known cure** for Alzheimer's disease, and damaged brain cells cannot yet be repaired or regenerated. "
                    "However, modern treatments and lifestyle interventions can slow progression and improve quality of life.\n\n"
                    "**What Modern Medicine Can Do:**\n"
                    "- **Slow Disease Progression:** Newer disease-modifying monoclonal antibodies (such as Lecanemab and Donanemab) target amyloid plaques to slow cognitive decline in early stages.\n"
                    "- **Manage Symptoms:** Medications like Donepezil and Memantine help maintain cognitive functioning, memory, and behavioral symptoms for a period of time.\n"
                    "- **Identify Reversible Mimics:** It is crucial to test for treatable causes of memory loss—such as vitamin B12 deficiency, thyroid disease, normal pressure hydrocephalus, sleep apnea, or medication side effects—which **can** be reversed when treated.\n\n"
                    "**Ongoing Research:**\n"
                    "Hundreds of clinical trials are currently investigating anti-tau therapies, neuroinflammation inhibitors, metabolic interventions, and early biomarker detection."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Alzheimer's Treatments", "url": "https://www.nia.nih.gov/health/alzheimers-medicines"},
                    {"name": "Alzheimer's Association Research Progress", "url": "https://www.alz.org"}
                ],
                "category": "cure_prognosis",
                "disclaimer": "Educational information on therapeutic status."
            }

        # -------------------------------------------------------------
        # 9. Early Signs & Symptoms / 10 Warning Signs
        # -------------------------------------------------------------
        if any(w in q for w in ["early sign", "early symptom", "warning sign", "warning symptom", "10 signs", "first sign", "first symptom", "signs of"]) or \
           ("symptom" in q and not any(w in q for w in ["treat", "medication", "cure"])) or \
           ("how to know" in q and any(w in q for w in ["alzheimer", "dementia", "has"])):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "The hallmark early symptom of Alzheimer's disease is difficulty remembering newly learned information, "
                    "because neuropathology typically begins in brain structures responsible for learning (the entorhinal cortex and hippocampus).\n\n"
                    "**The 10 Warning Signs (Alzheimer's Association):**\n"
                    "1. **Memory loss that disrupts daily life:** Repeating questions, forgetting important dates or recently learned facts.\n"
                    "2. **Challenges in planning or solving problems:** Difficulty following a familiar recipe or keeping track of bills.\n"
                    "3. **Difficulty completing familiar tasks:** Getting confused driving to a familiar grocery store or managing settings on a microwave.\n"
                    "4. **Confusion with time or place:** Losing track of dates, seasons, or how one arrived at a location.\n"
                    "5. **Trouble understanding visual images & spatial relationships:** Difficulty reading or judging distance while driving.\n"
                    "6. **New problems with words in speaking or writing:** Stopping mid-conversation, repeating stories, or calling items by the wrong name.\n"
                    "7. **Misplacing things and losing the ability to retrace steps:** Placing items in unusual places (e.g. keys in the freezer).\n"
                    "8. **Decreased or poor judgment:** Falling for financial scams or paying less attention to personal hygiene.\n"
                    "9. **Withdrawal from social activities:** Pulling away from hobbies, sports, or family gatherings.\n"
                    "10. **Changes in mood and personality:** Becoming suspicious, fearful, anxious, or easily upset when out of one's comfort zone.\n\n"
                    "**When to See a Doctor:**\n"
                    "If you observe several of these signs in yourself or a family member, arrange a medical consultation with a primary care doctor or neurologist."
                ),
                "sources": [
                    {"name": "Alzheimer's Association: 10 Early Signs", "url": "https://www.alz.org/alzheimers-dementia/10_signs"},
                    {"name": "National Institute on Aging: Alzheimer's Symptoms", "url": "https://www.nia.nih.gov"}
                ],
                "category": "symptoms_education",
                "disclaimer": "Educational screening checklist — consult a healthcare provider for diagnosis."
            }


        # -------------------------------------------------------------
        # 11. MCI & CDR 0.5 (Mild Cognitive Impairment)
        # -------------------------------------------------------------
        if any(w in q for w in ["mild cognitive impairment", "cdr 0.5", "very mild dementia", "what is mci"]) or \
           ("mci" in q.split() or "mci?" in q or "mci." in q or "mci," in q):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "**Mild Cognitive Impairment (MCI)**, often rated as **CDR 0.5 (Very Mild)**, is a clinical transitional state "
                    "between the cognitive changes of normal aging and the more pronounced deficits of dementia.\n\n"
                    "**Key Characteristics:**\n"
                    "- **Measurable Memory or Cognitive Decline:** Demonstrable on objective cognitive tests (e.g. MoCA or MMSE).\n"
                    "- **Preserved Functional Independence:** The individual can still perform essential daily living activities (cooking, driving, shopping, medication management), though complex tasks may take longer or require notes.\n"
                    "- **Progression Risk:** Approximately 10% to 15% of people with amnestic MCI progress to dementia each year. However, not everyone with MCI progresses; in some individuals, cognition remains stable or even improves if reversible causes are treated.\n\n"
                    "**Why Early Detection Matters:**\n"
                    "MCI is the optimal window for lifestyle interventions (aerobic exercise, cognitive engagement, cardiovascular control) and eligibility for new disease-modifying anti-amyloid therapies."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Mild Cognitive Impairment", "url": "https://www.nia.nih.gov/health/mild-cognitive-impairment"},
                    {"name": "Alzheimer's Association: MCI", "url": "https://www.alz.org"}
                ],
                "category": "mci_education",
                "disclaimer": "MCI is a clinical staging classification."
            }

        # -------------------------------------------------------------
        # 12. Clinical Dementia Rating (CDR) & Staging
        # -------------------------------------------------------------
        if any(w in q for w in ["stage", "stages", "staging", "phases", "cdr", "fast scale"]) or \
           any(p in q for p in ["mild dementia", "moderate dementia", "severe dementia", "clinical dementia rating", "how does it progress"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "The **Clinical Dementia Rating (CDR)** is a standardized global clinical rating scale used worldwide in dementia research and care "
                    "to quantify the severity of symptoms across 6 cognitive and functional domains.\n\n"
                    "**The 5 CDR Staging Levels:**\n"
                    "- **CDR 0.0 — Cognitively Normal:** No cognitive impairment; memory consistent with healthy aging.\n"
                    "- **CDR 0.5 — Very Mild Dementia / MCI:** Slight consistent forgetfulness, benign trouble with complex tasks, full daily independence.\n"
                    "- **CDR 1.0 — Mild Dementia:** Definite memory loss interfering with everyday life, difficulty managing finances or shopping independently, needs prompting for complex activities.\n"
                    "- **CDR 2.0 — Moderate Dementia:** Severe memory loss, disorientation to time and place, requires hands-on assistance with dressing, hygiene, and personal care.\n"
                    "- **CDR 3.0 — Severe Dementia:** Profound memory impairment, limited communication, complete dependence for physical care.\n\n"
                    "**How CDR Is Determined:**\n"
                    "CDR is rated through a semi-structured interview with both the patient and a reliable study partner/caregiver covering: Memory, Orientation, Judgment & Problem Solving, Community Affairs, Home & Hobbies, and Personal Care."
                ),
                "sources": [
                    {"name": "Washington University Knight ADRC: CDR Scoring", "url": "https://knightadrc.wustl.edu/cdr/cdr.htm"},
                    {"name": "National Institute on Aging: Alzheimer's Stages", "url": "https://www.nia.nih.gov"}
                ],
                "category": "alzheimer_staging",
                "disclaimer": "CDR is an interview-based clinical rating."
            }

        # -------------------------------------------------------------
        # 13. Normal Aging vs. Dementia ("Is forgetfulness normal?")
        # -------------------------------------------------------------
        if any(w in q for w in ["normal aging", "healthy aging", "senior moment", "age-related"]) or \
           ("forget" in q and any(w in q for w in ["normal", "aging", "old age", "worry", "senior", "age"])):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Occasional forgetfulness is a normal part of aging. The critical difference is that normal age-related memory lapses "
                    "do not disrupt daily functioning or worsen progressively over time.\n\n"
                    "**Normal Aging vs. Possible Dementia:**\n"
                    "| Typical Age-Related Changes | Possible Sign of Dementia |\n"
                    "| :--- | :--- |\n"
                    "| Forgetting names or appointments occasionally, but remembering them later. | Forgetting newly learned information and asking the same question repeatedly. |\n"
                    "| Sometimes making errors when balancing a checkbook. | Inability to manage household finances or follow numbers. |\n"
                    "| Occasionally needing help to record a TV show. | Inability to use familiar appliances (like a stove or telephone). |\n"
                    "| Temporarily misplacing keys or glasses. | Placing items in bizarre locations (e.g., wallet in the oven) and accusing others of theft. |\n"
                    "| Forgetting what day it is, but realizing it later. | Losing track of dates, seasons, or the passage of time entirely. |\n\n"
                    "**When to Consult a Physician:**\n"
                    "If memory lapses are noticed by family members or begin interfering with work, driving, or personal care, arrange a clinical evaluation."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Memory Loss & Normal Aging", "url": "https://www.nia.nih.gov/health/memory-loss-and-forgetfulness"},
                    {"name": "Alzheimer's Association: 10 Early Signs", "url": "https://www.alz.org"}
                ],
                "category": "normal_aging_comparison",
                "disclaimer": "Educational comparison — consult a physician for individual concerns."
            }

        # -------------------------------------------------------------
        # 14. Clinical Diagnosis & Tests (MoCA, MMSE, Biomarkers, PET)
        # -------------------------------------------------------------
        if any(w in q for w in ["mmse", "moca", "lumbar puncture", "blood test", "p-tau", "pet scan"]) or \
           (any(w in q for w in ["test", "tests", "testing", "diagnos", "screen", "evaluation"]) and \
            any(w in q for w in ["how", "doctor", "hospital", "clinic", "alzheimer", "dementia", "work", "conduct"])):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Diagnosing Alzheimer's disease requires a thorough medical evaluation combining cognitive assessments, neurological exams, "
                    "laboratory blood tests, and advanced neuroimaging.\n\n"
                    "**Core Components of a Diagnostic Evaluation:**\n"
                    "1. **Cognitive & Neuropsychological Screening:**\n"
                    "   - **MoCA (Montreal Cognitive Assessment):** 30-point screen sensitive to early impairment (executive function, memory, language).\n"
                    "   - **MMSE (Mini-Mental State Exam):** Widely used test for orientation, recall, and attention.\n"
                    "2. **Laboratory Blood Work:**\n"
                    "   - Complete blood count, Vitamin B12, thyroid panel (TSH), metabolic panel to exclude treatable metabolic mimics.\n"
                    "   - **Plasma Biomarkers (p-tau217):** High-accuracy blood tests currently entering clinical practice to measure tau and amyloid burden.\n"
                    "3. **Structural Neuroimaging (MRI / CT):**\n"
                    "   - Evaluates hippocampal atrophy, cortical volume loss, and rules out strokes, hydrocephalus, or tumors.\n"
                    "4. **Specialized Biomarker Tests (when indicated):**\n"
                    "   - **Amyloid / Tau PET Imaging:** Visualizes plaque and tangle deposits in living brain tissue.\n"
                    "   - **Cerebrospinal Fluid (CSF) Analysis:** Lumbar puncture measuring Aβ42/Aβ40 ratio and p-tau."
                ),
                "sources": [
                    {"name": "Alzheimer's Association Diagnostic Criteria", "url": "https://www.alz.org/alzheimers-dementia/diagnosis"},
                    {"name": "National Institute on Aging: Diagnostic Tests", "url": "https://www.nia.nih.gov"}
                ],
                "category": "clinical_testing",
                "disclaimer": "Diagnostic tests must be ordered and interpreted by a licensed medical provider."
            }

        # -------------------------------------------------------------
        # 15. Structural Brain MRI in Alzheimer's & Neuroimaging
        # -------------------------------------------------------------
        if (any(w in q for w in ["mri", "brain scan", "neuroimaging", "imaging"]) and not any(w in q for w in ["my result", "my scan", "uploaded"])) or \
           ("scan" in q and "alzheimer" in q):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Magnetic Resonance Imaging (MRI) is a critical neuroimaging modality in dementia evaluations. "
                    "It evaluates structural patterns of brain shrinkage (atrophy) and excludes other neurological causes of cognitive decline.\n\n"
                    "**Key Findings Evaluated on MRI:**\n"
                    "1. **Medial Temporal Lobe & Hippocampal Atrophy:** The hippocampus typically shows early volume loss in Alzheimer's disease.\n"
                    "2. **Enlargement of Ventricles:** As surrounding brain tissue atrophies, cerebrospinal fluid (CSF) filled lateral ventricles expand (ex-vacuo ventriculomegaly).\n"
                    "3. **Cortical Thinning & Sulcal Prominence:** Widening of brain crevices (sulci) across parietal and temporal lobes.\n"
                    "4. **Differential Diagnosis:** Crucial for identifying or ruling out brain tumors, subdural hematomas, normal pressure hydrocephalus (NPH), and vascular white matter lesions.\n\n"
                    "**Important Medical Clarification:**\n"
                    "An MRI scan alone cannot make a definitive diagnosis of Alzheimer's disease; it provides structural context that must be correlated with clinical cognitive tests and patient history."
                ),
                "sources": [
                    {"name": "Radiological Society of North America (RSNA): Neuroimaging in Dementia", "url": "https://www.rsna.org"},
                    {"name": "National Institute on Aging: Brain Imaging", "url": "https://www.nia.nih.gov"}
                ],
                "category": "mri_radiology",
                "disclaimer": "Radiology studies require certified radiologist interpretation."
            }

        # -------------------------------------------------------------
        # 16. Hippocampus, Brain Shrinkage & Atrophy
        # -------------------------------------------------------------
        if any(w in q for w in ["hippocamp", "atrophy", "brain shrink", "shrinkage", "ventricle", "ventricles", "white matter", "cortical thinning", "scheltens"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "The **hippocampus** is the brain's primary memory hub, located in the medial temporal lobe. "
                    "It is one of the earliest and most severely affected structures in Alzheimer's disease.\n\n"
                    "**Why Hippocampal Atrophy Occurs:**\n"
                    "- Tau neurofibrillary tangles originate in the transentorhinal and entorhinal cortex before spreading into the hippocampus.\n"
                    "- Loss of neurons in this area impairs the consolidation of short-term memories into long-term storage.\n"
                    "- In clinical radiology, physicians use visual grading scales such as the **Scheltens Medial Temporal Lobe Atrophy (MTA) score** (ranging from 0 to 4) to quantify hippocampal volume loss and choroid fissure widening.\n\n"
                    "**Technical Distinction for This Website's AI Tool:**\n"
                    "Our web application uses deep convolutional feature representations across whole axial slices for research staging; "
                    "it **does NOT perform automated 3D subcortical segmentation** or report explicit hippocampal volumes (which requires volumetric tools like FreeSurfer)."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Brain Changes in Alzheimer's", "url": "https://www.nia.nih.gov"},
                    {"name": "RSNA Neuroimaging Criteria", "url": "https://www.rsna.org"}
                ],
                "category": "neuroanatomy_atrophy",
                "disclaimer": "Research staging tool does not replace volumetric anatomical segmentation."
            }

        # -------------------------------------------------------------
        # 17. Lifestyle, Prevention & Risk Reduction
        # -------------------------------------------------------------
        if any(w in q for w in ["prevent", "prevention", "lifestyle", "exercise", "physical activity", "brain health", "habits"]) or \
           ("reduce" in q and "risk" in q) or ("lower" in q and "risk" in q):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "While there is no guaranteed prevention method, the **2024 Lancet Commission on Dementia** identified 14 modifiable risk factors "
                    "that account for nearly **45% of dementia cases worldwide**.\n\n"
                    "**Evidence-Based Risk Reduction Habits:**\n"
                    "1. **Cardiovascular Health:** What protects the heart protects the brain. Effectively treat hypertension, manage cholesterol, and control diabetes.\n"
                    "2. **Regular Physical Exercise:** 150 minutes per week of moderate aerobic exercise (brisk walking, swimming, cycling) promotes brain-derived neurotrophic factor (BDNF) and cerebral perfusion.\n"
                    "3. **Sensory & Hearing Care:** Treating mid-life hearing loss with hearing aids significantly reduces cognitive decline risk.\n"
                    "4. **Restorative Sleep:** Quality sleep (7–8 hours) enables the glymphatic system to clear metabolic waste products (including amyloid) from the brain.\n"
                    "5. **Cognitive Reserve:** Continually challenge the brain with novel skills, languages, reading, and puzzles.\n"
                    "6. **Social Engagement:** Strong interpersonal relationships and community involvement help buffer against depression and cognitive isolation.\n"
                    "7. **Avoid Toxins:** Stop smoking and limit alcohol consumption."
                ),
                "sources": [
                    {"name": "Lancet Commission on Dementia Prevention (2024)", "url": "https://www.thelancet.com"},
                    {"name": "World Health Organization: Dementia Risk Reduction", "url": "https://www.who.int"},
                    {"name": "Alzheimer's Association: Brain Health Habits", "url": "https://www.alz.org"}
                ],
                "category": "lifestyle_prevention",
                "disclaimer": "Healthy lifestyle supports brain resilience but does not guarantee immunity from neurodegenerative disease."
            }

        # -------------------------------------------------------------
        # 18. Diet, Nutrition & Supplements
        # -------------------------------------------------------------
        if any(w in q for w in ["diet", "food", "nutrition", "eat", "eating", "supplement", "supplements", "vitamin", "vitamins", "mind diet", "mediterranean diet", "omega 3", "ginkgo", "turmeric", "coconut oil"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Scientific research strongly supports dietary patterns rich in whole, anti-inflammatory foods—particularly the **MIND diet** and **Mediterranean diet**—for supporting long-term cognitive health.\n\n"
                    "**Evidence-Supported Dietary Recommendations:**\n"
                    "- **Green Leafy Vegetables:** Spinach, kale, and salads (at least 6 servings per week).\n"
                    "- **Berries:** Blueberries and strawberries contain high levels of anthocyanins and antioxidants.\n"
                    "- **Fatty Fish:** Salmon, sardines, and mackerel rich in Omega-3 fatty acids (DHA/EPA) support neuronal membrane integrity.\n"
                    "- **Healthy Fats:** Extra virgin olive oil as the primary cooking oil; walnuts and almonds for snacking.\n"
                    "- **Limit:** Red meat, butter, processed cheeses, pastries, sweets, and fried fast food.\n\n"
                    "**The Truth About 'Memory Supplements':**\n"
                    "Commercial over-the-counter memory supplements (such as ginkgo biloba, high-dose vitamin E, or coconut oil) have not demonstrated consistent disease-modifying efficacy in rigorous, double-blind clinical trials. "
                    "Always consult a physician before starting supplements, as some can interact with prescription blood thinners or cardiac medications."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Diet and Dementia", "url": "https://www.nia.nih.gov/health/what-do-we-know-about-diet-and-prevention-alzheimers-disease"},
                    {"name": "Alzheimer's Association: Nutrition Guidance", "url": "https://www.alz.org"}
                ],
                "category": "diet_nutrition",
                "disclaimer": "Nutritional habits support health but are not a medical cure or replacement for medical care."
            }

        # -------------------------------------------------------------
        # 19. Caregiver Support & Behavioral Tips
        # -------------------------------------------------------------
        if any(w in q for w in ["caregiver", "caregiving", "care for", "caring for", "agitation", "sundowning", "wandering", "burnout", "taking care"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Caring for an individual with Alzheimer's disease requires empathy, patience, structured routines, and essential self-care to prevent caregiver burnout.\n\n"
                    "**Practical Caregiver Strategies:**\n"
                    "1. **Communication Techniques:**\n"
                    "   - Use short, simple sentences and maintain gentle eye contact.\n"
                    "   - Avoid arguing or quizzing memory ('Don't you remember?'). Use validation and redirection instead.\n"
                    "2. **Managing Agitation & Sundowning:**\n"
                    "   - Keep a consistent daily routine for meals, activities, and bedtime.\n"
                    "   - Turn on indoor lighting before dusk to minimize disorientation and shadows.\n"
                    "3. **Home Safety:**\n"
                    "   - Remove trip hazards, install grab bars in bathrooms, and secure exterior doors if wandering is a risk.\n"
                    "4. **Caregiver Self-Care:**\n"
                    "   - Caregiver burnout is extremely common. Seek respite care services, support groups, and share responsibilities with family members or professional care providers."
                ),
                "sources": [
                    {"name": "Alzheimer's Association: Caregiver Resources", "url": "https://www.alz.org/help-support/caregiving"},
                    {"name": "National Institute on Aging: Caregiving Guidelines", "url": "https://www.nia.nih.gov/health/alzheimers-caregiving"}
                ],
                "category": "caregiver_guidance",
                "disclaimer": "Supportive educational advice for family caregivers."
            }

        # -------------------------------------------------------------
        # 20. When to See a Doctor & Specialist Referral
        # -------------------------------------------------------------
        if any(p in q for p in ["when to see a doctor", "when should i see a doctor", "specialist", "neurologist", "geriatrician", "who to consult", "should i see a doctor", "doctor appointment"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "You should seek a medical evaluation whenever memory lapses, language difficulties, or cognitive changes begin interfering with everyday life, work, or social relationships.\n\n"
                    "**Which Specialists to Consult:**\n"
                    "- **Primary Care Physician (PCP):** The recommended first step for baseline health checks, cognitive screening, and lab panels.\n"
                    "- **Neurologist:** Specialized physician focused on disorders of the brain and nervous system, neuroimaging interpretation, and dementia staging.\n"
                    "- **Geriatrician:** Specialist focusing on health and care in older adults, coordinating multi-condition management.\n"
                    "- **Neuropsychologist:** Conducts extensive cognitive testing (evaluating memory, attention, executive functioning, and processing speed).\n\n"
                    "**Preparing for Your Appointment:**\n"
                    "Write down observed changes, list all current medications/supplements, bring a family member or close friend to the visit, and bring previous brain imaging scans."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Doctor Visits for Memory Concerns", "url": "https://www.nia.nih.gov"},
                    {"name": "Alzheimer's Association: Finding a Doctor", "url": "https://www.alz.org"}
                ],
                "category": "medical_referral",
                "disclaimer": "Seek formal clinical evaluation for personalized diagnosis."
            }

        # -------------------------------------------------------------
        # 21. Life Expectancy, Progression & Prognosis
        # -------------------------------------------------------------
        if any(p in q for p in ["life expectancy", "how long do people live", "how long does someone live", "prognosis", "how fast does it progress", "survival", "end stage", "fatal", "die from"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "On average, individuals diagnosed with Alzheimer's disease live **4 to 8 years** after diagnosis, "
                    "though some individuals live 15 to 20 years depending on age, overall physical health, and quality of care.\n\n"
                    "**How Progression Varies:**\n"
                    "- **Variable Trajectory:** The rate of cognitive and physical decline varies widely among individuals.\n"
                    "- **Late-Stage Complications:** In severe Alzheimer's, complications often arise from loss of swallowing ability (dysphagia), aspiration pneumonia, immobility, and secondary infections.\n"
                    "- **Palliative Care:** Integrating supportive and palliative care early helps manage symptoms, enhance comfort, and preserve dignity for both patients and families."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Alzheimer's Progression & End of Life", "url": "https://www.nia.nih.gov"},
                    {"name": "Alzheimer's Association: Life Expectancy", "url": "https://www.alz.org"}
                ],
                "category": "prognosis_education",
                "disclaimer": "Prognosis varies significantly per individual. Consult the treating physician."
            }

        # -------------------------------------------------------------
        # 23. Early-Onset / Younger-Onset Alzheimer's
        # -------------------------------------------------------------
        if any(p in q for p in ["early onset", "young onset", "younger onset", "young people", "can a young person", "under 65", "in their 40s", "in their 50s", "in their 30s", "age 40", "age 50"]) or \
           ("year old" in q and any(num in q for num in ["20", "25", "30", "35", "40", "45", "50", "55", "60", "young"])):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Yes, Alzheimer's can affect younger people. When diagnosed in individuals **under age 65**, "
                    "it is termed **early-onset (or younger-onset) Alzheimer's**, representing approximately 5% to 10% of all cases.\n\n"
                    "**Key Characteristics:**\n"
                    "- **Age Range:** Most often diagnosed in people in their 40s and 50s, though very rare cases occur in the 30s.\n"
                    "- **Genetic Influence:** A higher proportion of younger-onset cases involve genetic mutations in the APP, PSEN1, or PSEN2 genes.\n"
                    "- **Atypical Presentation:** Younger patients frequently present with prominent executive, language, or visual-spatial difficulties rather than isolated memory loss.\n"
                    "- **Diagnostic Delays:** Because physicians may not initially suspect dementia in younger adults, symptoms are often mistakenly attributed to stress, depression, or burnout."
                ),
                "sources": [
                    {"name": "Alzheimer's Association: Younger-Onset Alzheimer's", "url": "https://www.alz.org/alzheimers-dementia/what-is-alzheimers/younger-early-onset"},
                    {"name": "National Institute on Aging: Early-Onset", "url": "https://www.nia.nih.gov"}
                ],
                "category": "young_onset_education",
                "disclaimer": "Educational information on younger-onset dementia."
            }

        # -------------------------------------------------------------
        # 23. This Website's AI Architecture & Technology (MobileNet, MC Dropout)
        # -------------------------------------------------------------
        if (any(w in q for w in ["model", "ai", "architecture", "algorithm", "pipeline", "network", "system", "technology", "accuracy"]) and \
            any(w in q for w in ["how", "work", "built", "train", "accurate", "performance", "mobilenet", "monte carlo", "uncertainty"])):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "NEUROSTAGE AI employs a lightweight deep learning architecture optimized for 3D structural MRI volume staging into 4 clinical classes "
                    "(Non-Demented, Very Mild, Mild, Moderate Dementia).\n\n"
                    "**Technical Architecture Pipeline:**\n"
                    "1. **3D Volume Preprocessing:** Loads NIfTI (.nii/.nii.gz) scans, extracts informative axial 2D cross-sections (filtering background skull/air slices), and resizes them to 224×224 RGB.\n"
                    "2. **Convolutional Backbone (MobileNet):** Uses depthwise separable convolutions for high compute efficiency, extracting deep spatial representations of brain morphology.\n"
                    "3. **Patient-Level Aggregation:** Slices are classified individually and pooled using patient-level **mean probability aggregation** across all valid slices.\n"
                    "4. **Monte Carlo Dropout Uncertainty:** Runs 20 stochastic dropout forward passes at inference to compute **predictive Shannon entropy**, quantifying the model's epistemic uncertainty.\n"
                    "5. **Zero Data Leakage:** Validated using patient-grouped 5-fold cross-validation on the OASIS-1 dataset."
                ),
                "sources": [
                    {"name": "NEUROSTAGE AI Technical Architecture Documentation", "url": "https://github.com"},
                    {"name": "OASIS Brains Benchmark Dataset", "url": "https://www.oasis-brains.org"}
                ],
                "category": "technical_architecture",
                "disclaimer": "Academic research prototype pipeline."
            }

        # -------------------------------------------------------------
        # 24. OASIS-1 Dataset
        # -------------------------------------------------------------
        if "oasis" in q or ("dataset" in q and "train" in q) or "oasis-1" in q:
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "The model was trained and evaluated on the **OASIS-1 (Open Access Series of Imaging Studies)** dataset, "
                    "a publicly available neuroimaging benchmark provided by Washington University in St. Louis.\n\n"
                    "**Dataset Details:**\n"
                    "- **Subjects:** 416 subjects aged 18 to 96 years.\n"
                    "- **Modality:** T1-weighted structural magnetic resonance imaging (MRI).\n"
                    "- **Staging Annotations:** Ground-truth Clinical Dementia Rating (CDR) scores assigned through clinical evaluations:\n"
                    "  - CDR 0.0 (Non-Demented)\n"
                    "  - CDR 0.5 (Very Mild Dementia)\n"
                    "  - CDR 1.0 (Mild Dementia)\n"
                    "  - CDR 2.0 (Moderate Dementia)\n"
                    "- **Split Integrity:** Rigid subject-level partitioning ensures that no slices from the same subject appear in both training and test sets."
                ),
                "sources": [
                    {"name": "OASIS Brains Project", "url": "https://www.oasis-brains.org"},
                    {"name": "Washington University Knight ADRC", "url": "https://knightadrc.wustl.edu"}
                ],
                "category": "dataset_information",
                "disclaimer": "OASIS-1 is an open-access neuroimaging research resource."
            }

        # -------------------------------------------------------------
        # 25. Sleep & Brain Clearance (Glymphatic System)
        # -------------------------------------------------------------
        if any(w in q for w in ["sleep", "insomnia", "glymphatic", "deep sleep", "sleep apnea"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "High-quality sleep is crucial for cognitive health because during deep slow-wave sleep, the brain activates the "
                    "**glymphatic system**—a specialized waste clearance pathway that removes metabolic byproducts, including amyloid-beta and tau.\n\n"
                    "**Scientific Insights:**\n"
                    "- **Waste Clearance:** Cerebrospinal fluid (CSF) pulses through interstitial spaces during slow-wave sleep, flushing out toxic aggregates.\n"
                    "- **Sleep Apnea Risk:** Obstructive sleep apnea (OSA) causes chronic nocturnal hypoxia and fragmented sleep, significantly increasing the risk of cognitive decline. Treating OSA with CPAP therapy supports cognitive function.\n"
                    "- **Sleep Hygiene:** Maintain a consistent sleep schedule (7 to 8 hours), keep the bedroom cool and dark, and avoid screens and caffeine before bedtime."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Sleep and Cognitive Health", "url": "https://www.nia.nih.gov"},
                    {"name": "Alzheimer's Association: Sleep Research", "url": "https://www.alz.org"}
                ],
                "category": "sleep_science",
                "disclaimer": "Educational information on sleep neurology."
            }

        # -------------------------------------------------------------
        # 26. Memory Loss & Forgetting
        # -------------------------------------------------------------
        if any(w in q for w in ["memory loss", "losing memory", "short term memory", "forgetting names", "can't remember", "cannot remember", "trouble remembering"]):
            return {
                "answer": (
                    "**Short Answer:**\n"
                    "Memory loss can result from a wide range of factors, ranging from normal age-related slowing to acute stress, "
                    "sleep deprivation, nutritional deficiencies, or progressive neurodegenerative conditions like Alzheimer's disease.\n\n"
                    "**Types of Memory Changes:**\n"
                    "- **Short-Term vs. Long-Term:** Alzheimer's disease typically attacks recent episodic memory first (events from earlier today or yesterday), while memories from childhood often remain vivid until later stages.\n"
                    "- **Reversible Causes:** Medical providers routinely check for Vitamin B12 deficiency, hypothyroidism, depression (pseudodementia), polypharmacy interactions, and urinary tract infections in older adults.\n"
                    "- **When to Worry:** When memory difficulties disrupt routine tasks (such as forgetting how to navigate home or struggling with stove knobs), professional medical evaluation is indicated."
                ),
                "sources": [
                    {"name": "National Institute on Aging: Memory Loss", "url": "https://www.nia.nih.gov/health/memory-loss-and-forgetfulness"},
                    {"name": "Alzheimer's Association: Memory Concerns", "url": "https://www.alz.org"}
                ],
                "category": "memory_loss_education",
                "disclaimer": "Educational information on memory and cognitive function."
            }

        # -------------------------------------------------------------
        # 27. Dynamic Contextual Synthesizer (Intelligent Fallback)
        # -------------------------------------------------------------
        # Extract meaningful content words from user message
        stop_words = {"the", "and", "for", "that", "this", "with", "what", "how", "can", "why", "are", "you", "about", "tell", "does", "from", "have", "some", "your"}
        words = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", q) if w not in stop_words]
        topic_preview = ", ".join(words[:4]) if words else "your question"

        return {
            "answer": (
                f"**Short Answer:**\n"
                f"Regarding **'{message.strip()}'**: In the clinical context of cognitive health and Alzheimer's disease, "
                f"evidence emphasizes understanding the distinction between research observations and individualized medical care.\n\n"
                f"**Clinical Context & Scientific Evidence:**\n"
                f"- **Neurological Basis:** Alzheimer's disease involves progressive accumulation of beta-amyloid plaques and tau neurofibrillary tangles, "
                f"leading to synaptic dysfunction and brain atrophy over several years.\n"
                f"- **Evaluating '{topic_preview}':** Clinical specialists address cognitive and neurological questions through comprehensive assessment, "
                f"including validated screening tools (MoCA/MMSE), laboratory testing to exclude reversible conditions, and diagnostic MRI imaging.\n"
                f"- **Research Insights:** Research platforms and AI staging tools provide population-level algorithmic insights, but individual medical decisions "
                f"must be guided by certified clinical practitioners.\n\n"
                f"**What You Can Do:**\n"
                f"- You can explore the **MRI Analysis** tab to observe how deep learning models evaluate structural axial slices and uncertainty estimation.\n"
                f"- Check the **Architecture** tab to review model performance metrics across 5-fold cross-validation.\n"
                f"- If you or a loved one have personal health symptoms or questions, consult a neurologist or primary care physician."
            ),
            "sources": DEFAULT_SOURCES[:2],
            "category": "clinical_knowledge_base",
            "disclaimer": "Educational medical information — not a personal diagnosis or medical recommendation."
        }

    async def get_response(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        mri_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user message, evaluate emergency triage, and generate evidence-based response.
        Tries OpenAI / Groq / Gemini LLMs if valid keys are available and not circuit-broken,
        and reliably falls back to the comprehensive Clinical Knowledge Base engine.
        """
        # 1. Immediate emergency screening
        emergency = self._check_emergency(message)
        if emergency:
            return emergency

        context_addon = self._format_mri_context_prompt(mri_context)
        full_system_prompt = SYSTEM_PROMPT + context_addon
        now = time.time()

        # 2. If valid OpenAI API key is available and not circuit-broken
        if self.openai_key and not self.openai_key.startswith("your_") and len(self.openai_key) > 20 and now > self._openai_disabled_until:
            try:
                messages_payload = [{"role": "system", "content": full_system_prompt}]
                if history:
                    for turn in history[-6:]:
                        role = "user" if turn.get("sender") == "user" else "assistant"
                        text = turn.get("text") or turn.get("message") or ""
                        if text:
                            messages_payload.append({"role": role, "content": text})
                messages_payload.append({"role": "user", "content": message})

                headers = {
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": messages_payload,
                    "temperature": 0.2,
                    "max_tokens": 1000
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data["choices"][0]["message"]["content"]
                        return {
                            "answer": text,
                            "sources": DEFAULT_SOURCES,
                            "category": "openai_generated",
                            "disclaimer": "Medical information only — not a clinical diagnosis."
                        }
                    elif resp.status_code in (401, 402, 429):
                        self._openai_disabled_until = now + 600.0  # Cool off for 10 min
                        print(f"[MedicalChatProvider] OpenAI returned {resp.status_code}. Circuit breaker activated for 10 minutes.")
            except Exception as e:
                self._openai_disabled_until = now + 60.0
                print(f"[MedicalChatProvider] OpenAI call failed ({str(e)}). Circuit breaker activated.")

        # 3. If valid Groq API key is available and not circuit-broken
        if self.groq_key and not self.groq_key.startswith("your_") and now > self._groq_disabled_until:
            try:
                messages_payload = [{"role": "system", "content": full_system_prompt}]
                if history:
                    for turn in history[-6:]:
                        role = "user" if turn.get("sender") == "user" else "assistant"
                        text = turn.get("text") or turn.get("message") or ""
                        if text:
                            messages_payload.append({"role": role, "content": text})
                messages_payload.append({"role": "user", "content": message})

                headers = {
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": messages_payload,
                    "temperature": 0.2,
                    "max_tokens": 1000
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data["choices"][0]["message"]["content"]
                        return {
                            "answer": text,
                            "sources": DEFAULT_SOURCES,
                            "category": "groq_generated",
                            "disclaimer": "Medical information only — not a clinical diagnosis."
                        }
                    elif resp.status_code in (401, 402, 429):
                        self._groq_disabled_until = now + 600.0
                        print(f"[MedicalChatProvider] Groq returned {resp.status_code}. Circuit breaker activated.")
            except Exception as e:
                self._groq_disabled_until = now + 60.0
                print(f"[MedicalChatProvider] Groq call failed ({str(e)}). Circuit breaker activated.")

        # 4. If valid Gemini API key is available and not circuit-broken
        if self.gemini_key and now > self._gemini_disabled_until:
            try:
                contents = []
                if history:
                    for turn in history[-6:]:
                        role = "user" if turn.get("sender") == "user" else "model"
                        text = turn.get("text") or turn.get("message") or ""
                        if text:
                            contents.append({"role": role, "parts": [{"text": text}]})

                contents.append({"role": "user", "parts": [{"text": message}]})

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
                payload = {
                    "systemInstruction": {"parts": [{"text": full_system_prompt}]},
                    "contents": contents,
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 1000
                    }
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return {
                            "answer": text,
                            "sources": DEFAULT_SOURCES,
                            "category": "gemini_generated",
                            "disclaimer": "Medical information only — not a clinical diagnosis."
                        }
                    elif resp.status_code in (400, 401, 403, 429):
                        self._gemini_disabled_until = now + 600.0
                        print(f"[MedicalChatProvider] Gemini returned {resp.status_code}. Circuit breaker activated.")
            except Exception as e:
                self._gemini_disabled_until = now + 60.0
                print(f"[MedicalChatProvider] Gemini call failed ({str(e)}). Circuit breaker activated.")

        # 5. Deterministic Evidence-Based Clinical Knowledge Base
        return self._build_knowledge_base_response(message, mri_context)


# Global singleton instance
_chat_provider: Optional[MedicalChatProvider] = None


def get_chat_provider() -> MedicalChatProvider:
    global _chat_provider
    if _chat_provider is None:
        _chat_provider = MedicalChatProvider()
    return _chat_provider
