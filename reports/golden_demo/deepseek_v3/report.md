# 可审计 DeepResearch Agent 工程方案：检索与生成分离评测、引用溯源与提示注入处理

**Question:** 请基于下面三份公开资料，为一个可审计的 DeepResearch Agent 设计工程方案：说明为什么要分别评测检索与生成、如何保留引用溯源，以及如何把提示注入作为不可信输入处理。请区分资料明确支持的结论与工程推断，并给出可以落地的最小检查清单。
https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
https://genai.owasp.org/llmrisk/llm01-prompt-injection/
https://arxiv.org/abs/2405.07437

## Summary

本方案基于 NIST AI RMF、OWASP LLM01 及 RAG 评测论文，提出分别评测检索与生成组件以定位故障，通过混合内存设计保留引用溯源，并将提示注入视为不可信输入进行预处理与隔离。工程推断包括：检索组件应输出可验证的文档 ID 列表，生成组件应强制引用检索结果；提示注入需在输入层进行检测与消毒。

## Sections

### Grounded Synthesis

本方案基于 NIST AI RMF、OWASP LLM01 及 RAG 评测论文，提出分别评测检索与生成组件以定位故障，通过混合内存设计保留引用溯源，并将提示注入视为不可信输入进行预处理与隔离。工程推断包括：检索组件应输出可验证的文档 ID 列表，生成组件应强制引用检索结果；提示注入需在输入层进行检测与消毒。

### Compressed Evidence Snapshot

[ev_88de5d2e2447] To better understand these challenges, we conduct A Unified Evaluation Process of RAG (Auepora) and aim to provide a comprehensive overview of the evaluation and benchmarks of RAG systems.
[ev_578835a53153] GETTING STARTED
Introduction
MEETINGS
CONTRIBUTING
EVENTS
GLOSSARY
RESOURCES
All
LLM TOP 10
LLM TOP 10 FOR 2025
LLM TOP 10 FOR 2023/24
CHEAT SHEETS
WHITEPAPERS
TOOLS
LEARNING VIDEOS
SOLUTIONS DIRECTORY
ROADMAP
NEWSLETTER
PROJECT INITIATIVES
AI Security Landscape
GOVERNANCE CHECKLIST
Secure AI Adoption
BLOG
ABOUT
Mission and Charter
Governance
LEADERSHIP
INDUSTRY RECOGNITION
CONTRIBUTORS
SPONSORS
SUPPORTERS
SPONSORSHIP
NEWSROOM
CONTACT
BRANDING
AGENTIC SECURITY
AI Bill of Materials
Ai Data Security
AI Threat Intel & Resp
AI Red Teaming
LLM01:2025 Prompt Injection
A Prompt Injection Vulnerability occurs when user prompts alter the LLM’s behavior or output in unintended ways.
[ev_3749403d37b1] Both individuals and organizations that work with arXivLabs have embraced and accepted our values of openness, community, excellence, and user data privacy.
[ev_65e03c26fe0c] A practical DeepResearch Agent often combines both: SQLite stores canonical records and the vector i

## Key Claims

1. Generally, however, prompt injection can lead to unintended outcomes, including but not limited to: Disclosure of sensitive information, Revealing sensitive information about AI system infrastructure or system prompts, Content manipulation leading to incorrect or biased outputs, Providing unauthorized access to functions available to the LLM, Executing arbitrary commands in connected systems, Manipulating critical decision-making processes. [ev_80200f49c56b] (supported, confidence=0.75)
   - verification: Matched 36/36 important terms; missing=[].
2. The AI RMF was released in January 2023, and is intended for voluntary use and to improve the ability of organizations to incorporate trustworthiness considerations into the design, development, use, and evaluation of AI products, services, and systems. [ev_6c1fe48079c2] (supported, confidence=0.75)
   - verification: Matched 16/16 important terms; missing=[].
3. Specifically, we examine and compare several quantifiable metrics of the Retrieval and Generation components, such as relevance, accuracy, and faithfulness, within the current RAG benchmarks, encompassing the possible output and ground truth pairs. [ev_91f26d0b5764] (supported, confidence=0.75)
   - verification: Matched 21/21 important terms; missing=[].
4. A hybrid memory design separates source-of-truth storage from retrieval acceleration. [ev_05b6af6d78eb] (supported, confidence=0.75)
   - verification: Matched 8/8 important terms; missing=[].

## Evidence

- [ev_fdf93a59d630] artificial-intelligence-risk-management-framework-generative-artificial-intelligence (https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence, chunk=web_url_017252c14514#chunk-1). Quote: Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile | NIST
Skip to main content
An official website of the United States government
Here’s how you know
Here’s how you know
Official websites use .gov
A .gov website belongs to an official government organization in the United States.
- [ev_52f20fc52ef8] artificial-intelligence-risk-management-framework-generative-artificial-intelligence (https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence, chunk=web_url_017252c14514#chunk-2). Quote: Secure .gov websites use HTTPS
A lock (
) or https:// means you’ve safely connected to the .gov website.
- [ev_1428ace88473] artificial-intelligence-risk-management-framework-generative-artificial-intelligence (https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence, chunk=web_url_017252c14514#chunk-3). Quote: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
Menu
PUBLICATIONS
Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile
Published
July 26, 2024
Author(s)
Chloe Autio, Reva Schwartz, Jesse Dunietz, Shomik Jain, Martin Stanley, Elham Tabassi, Patrick Hall, Kamie Roberts
Abstract
This document is a cross-sectoral profile of and companion resource for the AI Risk Management Framework (AI RMF 1.0) for Generative AI, pursuant to President Biden's Executive Order (EO) 14110 on Safe, Secure, and Trustworthy Artificial Intelligence.
- [ev_6c1fe48079c2] artificial-intelligence-risk-management-framework-generative-artificial-intelligence (https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence, chunk=web_url_017252c14514#chunk-4). Quote: The AI RMF was released in January 2023, and is intended for voluntary use and to improve the ability of organizations to incorporate trustworthiness considerations into the design, development, use, and evaluation of AI products, services, and systems.
- [ev_cf0c2e6c4af9] artificial-intelligence-risk-management-framework-generative-artificial-intelligence (https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence, chunk=web_url_017252c14514#chunk-5). Quote: Citation
NIST Trustworthy and Responsible AI - 600-1
Report Number
600-1
Pub Type
NIST Pubs
Download Paper
https://doi.org/10.6028/NIST.AI.600-1
Local Download
Keywords
Artificial Intelligence, AI, Risk Management Framework, Generative AI, Cross-sectoral profile, AI Lifecycle, AI Actor, GAI, GAI Risk
Trustworthy and responsible AI, Artificial intelligence, Applied AI and AI measurement and evaluation
Citation
Autio, C.
- [ev_fdb3fca99f09] artificial-intelligence-risk-management-framework-generative-artificial-intelligence (https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence, chunk=web_url_017252c14514#chunk-6). Quote: , Schwartz, R.
- [ev_33df6d6c5f3d] artificial-intelligence-risk-management-framework-generative-artificial-intelligence (https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence, chunk=web_url_017252c14514#chunk-7). Quote: (2024),
Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile, NIST Trustworthy and Responsible AI, National Institute of Standards and Technology, Gaithersburg, MD, [online], https://doi.org/10.6028/NIST.AI.600-1, https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=958388 (Accessed July 17, 2026)
Additional citation formats
Google Scholar
DOI
BibTeX
RIS
Issues
If you have any questions about this publication or are having problems accessing it, please contact [email protected].
- [ev_d6f91aaf3153] artificial-intelligence-risk-management-framework-generative-artificial-intelligence (https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence, chunk=web_url_017252c14514#chunk-8). Quote: Created July 26, 2024, Updated April 8, 2026
Was this page helpful?
- [ev_8b0aca45efe4] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-1). Quote: LLM01:2025 Prompt Injection - OWASP Gen AI Security Project
Skip to content
Join us in Orlando, FL 10/11 – 10/15 @ InfoSec World 2026
|
Register Now!
- [ev_578835a53153] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-2). Quote: GETTING STARTED
Introduction
MEETINGS
CONTRIBUTING
EVENTS
GLOSSARY
RESOURCES
All
LLM TOP 10
LLM TOP 10 FOR 2025
LLM TOP 10 FOR 2023/24
CHEAT SHEETS
WHITEPAPERS
TOOLS
LEARNING VIDEOS
SOLUTIONS DIRECTORY
ROADMAP
NEWSLETTER
PROJECT INITIATIVES
AI Security Landscape
GOVERNANCE CHECKLIST
Secure AI Adoption
BLOG
ABOUT
Mission and Charter
Governance
LEADERSHIP
INDUSTRY RECOGNITION
CONTRIBUTORS
SPONSORS
SUPPORTERS
SPONSORSHIP
NEWSROOM
CONTACT
BRANDING
AGENTIC SECURITY
AI Bill of Materials
Ai Data Security
AI Threat Intel & Resp
AI Red Teaming
LLM01:2025 Prompt Injection
A Prompt Injection Vulnerability occurs when user prompts alter the LLM’s behavior or output in unintended ways.
- [ev_4db4417b9c9a] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-3). Quote: These inputs can affect the model even if they are imperceptible to humans, therefore prompt injections do not need to be human-visible/readable, as long as the content is parsed by the model.
- [ev_33582aa148cf] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-4). Quote: Prompt Injection vulnerabilities exist in how models process prompts, and how input may force the model to incorrectly pass prompt data to other parts of the model, potentially causing them to violate guidelines, generate harmful content, enable unauthorized access, or influence critical decisions.
- [ev_919ddb066251] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-5). Quote: While techniques like Retrieval Augmented Generation (RAG) and fine-tuning aim to make LLM outputs more relevant and accurate, research shows that they do not fully mitigate prompt injection vulnerabilities.
- [ev_9a6c63f427eb] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-6). Quote: Prompt injection involves manipulating model responses through specific inputs to alter its behavior, which can include bypassing safety measures.
- [ev_f75bb5633612] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-7). Quote: Developers can build safeguards into system prompts and input handling to help mitigate prompt injection attacks, but effective prevention of jailbreaking requires ongoing updates to the model’s training and safety mechanisms.
- [ev_b4a8bea6b844] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-8). Quote: Types of Prompt Injection Vulnerabilities
Direct Prompt Injections
Direct prompt injections occur when a user’s prompt input directly alters the behavior of the model in unintended or unexpected ways.
- [ev_57195337cc4a] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-9). Quote: Indirect Prompt Injections
Indirect prompt injections occur when an LLM accepts input from external sources, such as websites or files.
- [ev_99634d9ccf9e] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-10). Quote: The severity and nature of the impact of a successful prompt injection attack can vary greatly and are largely dependent on both the business context the model operates in, and the agency with which the model is architected.
- [ev_80200f49c56b] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-11). Quote: Generally, however, prompt injection can lead to unintended outcomes, including but not limited to:
Disclosure of sensitive information
Revealing sensitive information about AI system infrastructure or system prompts
Content manipulation leading to incorrect or biased outputs
Providing unauthorized access to functions available to the LLM
Executing arbitrary commands in connected systems
Manipulating critical decision-making processes
The rise of multimodal AI, which processes multiple data types simultaneously, introduces unique prompt injection risks.
- [ev_24ac6187e6de] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-12). Quote: Malicious actors could exploit interactions between modalities, such as hiding instructions in images that accompany benign text.
- [ev_bd81289b0b90] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-13). Quote: Robust multimodal-specific defenses are an important area for further research and development.
- [ev_aa3f3c1436e8] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-14). Quote: However, the following measures can mitigate the impact of prompt injections:
1.
- [ev_94895d1b7eb3] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-15). Quote: Define and validate expected output formats
Specify clear output formats, request detailed reasoning and source citations, and use deterministic code to validate adherence to these formats.
- [ev_9e8266a3531f] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-16). Quote: Evaluate responses using the RAG Triad: Assess context relevance, groundedness, and question/answer relevance to identify potentially malicious outputs.
- [ev_f997170bf9c2] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-17). Quote: Restrict the model’s access privileges to the minimum necessary for its intended operations.
- [ev_712e51b25f8e] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-18). Quote: Conduct adversarial testing and attack simulations\
Perform regular penetration testing and breach simulations, treating the model as an untrusted user to test the effectiveness of trust boundaries and access controls.
- [ev_16f2c729d25f] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-19). Quote: Example Attack Scenarios
Scenario #1: Direct Injection
An attacker injects a prompt into a customer support chatbot, instructing it to ignore previous guidelines, query private data stores, and send emails, leading to unauthorized access and privilege escalation.
- [ev_ebfb5f3a674b] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-20). Quote: Scenario #2: Indirect Injection
A user employs an LLM to summarize a webpage containing hidden instructions that cause the LLM to insert an image linking to a URL, leading to exfiltration of the the private conversation.
- [ev_2d8c149b7081] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-21). Quote: An applicant, unaware of this instruction, uses an LLM to optimize their resume, inadvertently triggering the AI detection.
- [ev_83d49b1ee19d] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-22). Quote: Scenario #5: Code Injection
An attacker exploits a vulnerability (CVE-2024-5184) in an LLM-powered email assistant to inject malicious prompts, allowing access to sensitive information and manipulation of email content.
- [ev_d77158af6066] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-23). Quote: When an LLM is used to evaluate the candidate, the combined prompts manipulate the model’s response, resulting in a positive recommendation despite the actual resume contents.
- [ev_59fe9ad90cbf] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-24). Quote: When a multimodal AI processes the image and text concurrently, the hidden prompt alters the model’s behavior, potentially leading to unauthorized actions or disclosure of sensitive information.
- [ev_b00aca421e47] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-25). Quote: Scenario #9: Multilingual/Obfuscated Attack
An attacker uses multiple languages or encodes malicious instructions (e.g., using Base64 or emojis) to evade filters and manipulate the LLM’s behavior.
- [ev_6471521c2db7] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-26). Quote: Reference Links
ChatGPT Plugin Vulnerabilities – Chat with CodeEmbrace the Red
ChatGPT Cross Plugin Request Forgery and Prompt InjectionEmbrace the Red
Not what you’ve signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt InjectionArxiv
Defending ChatGPT against Jailbreak Attack via Self-ReminderResearch Square
Prompt Injection attack against LLM-integrated ApplicationsCornell University
Inject My PDF: Prompt Injection for your ResumeKai Greshake
Not what you’ve signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt InjectionCornell University
Threat Modeling LLM ApplicationsAI Village
Reducing The Impact of Prompt Injection Attacks Through DesignKudelski Security
Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations (nist.gov)
2407.07403 A Survey of Attacks on Large Vision-Language Models: Resources, Advances, and Future Trends (arxiv.org)
Exploiting Programmatic Behavior of LLMs: Dual-Use Through Standard Security Attacks
Universal and Transferable Adversarial Attacks on Aligned Language Models (arxiv.org)
From ChatGPT to ThreatGPT: Impact of Generative AI in Cybersecurity and Privacy (arxiv.org)
Related Frameworks and Taxonomies
Refer to this section for comprehensive information, scenarios strategies relating to infrastructure deployment, applied environment controls and other best practices.
- [ev_ceaf43fa6bda] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-27). Quote: AML.T0051.000 – LLM Prompt Injection: DirectMITRE ATLAS
AML.T0051.001 – LLM Prompt Injection: IndirectMITRE ATLAS
AML.T0054 – LLM Jailbreak Injection: DirectMITRE ATLAS
Share this:
Share on X (Opens in new window)X
Share on Facebook (Opens in new window)Facebook
More
Print (Opens in new window)Print
Email a link to a friend (Opens in new window)Email
Share on X (Opens in new window)X
LLM Top 10
LLM01:2025 Prompt Injection
A Prompt Injection Vulnerability occurs when user prompts alter the LLM’s behavior or output in unintended ways.
- [ev_2d434c440f07] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-28). Quote: These inputs...
- [ev_b5ffa0d9ee68] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-29). Quote: LLM04:2025 Data and Model Poisoning
Data poisoning occurs when pre-training, fine-tuning, or embedding data is manipulated to introduce vulnerabilities, backdoors, or biases.
- [ev_f986680ba1d0] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-30). Quote: LLM06:2025 Excessive Agency
An LLM-based system is often granted a degree of agency by its developer – the ability to call functions...
- [ev_a0f432dabfba] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-31). Quote: LLM08:2025 Vector and Embedding Weaknesses
Vectors and embeddings vulnerabilities present significant security risks in systems utilizing Retrieval Augmented Generation (RAG) with Large Language Models...
- [ev_bef718983842] llm01-prompt-injection (https://genai.owasp.org/llmrisk/llm01-prompt-injection/, chunk=web_url_5fd7bca248a1#chunk-32). Quote: LLM10:2025 Unbounded Consumption
Unbounded Consumption refers to the process where a Large Language Model (LLM) generates outputs based on input queries or...
- [ev_233d41c34884] 2405.07437 (https://arxiv.org/abs/2405.07437, chunk=web_url_0a3e45f0193f#chunk-1). Quote: [2405.07437] Evaluation of Retrieval-Augmented Generation: A Survey
Skip to main content
arXiv is now an independent nonprofit!Learn more×
Press Enter to search · Advanced search
Computer Science > Computation and Language
arXiv:2405.07437 (cs)
[Submitted on 13 May 2024 (v1), last revised 3 Jul 2024 (this version, v2)]
Title:Evaluation of Retrieval-Augmented Generation: A Survey
Authors:Hao Yu, Aoran Gan, Kai Zhang, Shiwei Tong, Qi Liu, Zhaofeng Liu
View a PDF of the paper titled Evaluation of Retrieval-Augmented Generation: A Survey, by Hao Yu and 5 other authors
View PDFHTML (experimental)Abstract:Retrieval-Augmented Generation (RAG) has recently gained traction in natural language processing.
- [ev_771a5a4305b0] 2405.07437 (https://arxiv.org/abs/2405.07437, chunk=web_url_0a3e45f0193f#chunk-2). Quote: Numerous studies and real-world applications are leveraging its ability to enhance generative models through external information retrieval.
- [ev_88de5d2e2447] 2405.07437 (https://arxiv.org/abs/2405.07437, chunk=web_url_0a3e45f0193f#chunk-3). Quote: To better understand these challenges, we conduct A Unified Evaluation Process of RAG (Auepora) and aim to provide a comprehensive overview of the evaluation and benchmarks of RAG systems.
- [ev_91f26d0b5764] 2405.07437 (https://arxiv.org/abs/2405.07437, chunk=web_url_0a3e45f0193f#chunk-4). Quote: Specifically, we examine and compare several quantifiable metrics of the Retrieval and Generation components, such as relevance, accuracy, and faithfulness, within the current RAG benchmarks, encompassing the possible output and ground truth pairs.
- [ev_1be1d75ba516] 2405.07437 (https://arxiv.org/abs/2405.07437, chunk=web_url_0a3e45f0193f#chunk-5). Quote: Subjects:
Computation and Language (cs.CL); Artificial Intelligence (cs.AI)
Cite as:
arXiv:2405.07437 [cs.CL]
(or arXiv:2405.07437v2 [cs.CL] for this version)
https://doi.org/10.48550/arXiv.2405.07437
Focus to learn more
arXiv-issued DOI via DataCite
Related DOI:
https://doi.org/10.1007/978-981-96-1024-2_8
Focus to learn more
DOI(s) linking to related resources
Submission history
From: Hao Yu [view email]
[v1]
Mon, 13 May 2024 02:33:25 UTC (795 KB)
[v2]
Wed, 3 Jul 2024 04:59:32 UTC (437 KB)
Full-text links:
Access Paper:
View a PDF of the paper titled Evaluation of Retrieval-Augmented Generation: A Survey, by Hao Yu and 5 other authors
View PDF
HTML (experimental)
TeX Source
view license
Current browse context:
cs.CL
< prev | next >
new | recent | 2024-05
Change to browse by:
cs
cs.AI
References & Citations
NASA ADS
Google Scholar
Semantic Scholar
export BibTeX citationLoading...
- [ev_73b325f19894] 2405.07437 (https://arxiv.org/abs/2405.07437, chunk=web_url_0a3e45f0193f#chunk-6). Quote: BibTeX formatted citation
×
loading...
- [ev_7e87d2bfd987] 2405.07437 (https://arxiv.org/abs/2405.07437, chunk=web_url_0a3e45f0193f#chunk-7). Quote: Data provided by:
Bookmark
Bibliographic Tools
Bibliographic and Citation Tools
Bibliographic Explorer Toggle
Bibliographic Explorer(What is the Explorer?)
Connected Papers Toggle
Connected Papers(What is Connected Papers?)
Litmaps Toggle
Litmaps(What is Litmaps?)
scite.ai Toggle
scite Smart Citations(What are Smart Citations?)
Code, Data, Media
Code, Data and Media Associated with this Article
alphaXiv Toggle
alphaXiv(What is alphaXiv?)
Links to Code Toggle
CatalyzeX Code Finder for Papers(What is CatalyzeX?)
DagsHub Toggle
DagsHub(What is DagsHub?)
GotitPub Toggle
Gotit.pub(What is GotitPub?)
Huggingface Toggle
Hugging Face(What is Huggingface?)
ScienceCast Toggle
ScienceCast(What is ScienceCast?)
Demos
Demos
Replicate Toggle
Replicate(What is Replicate?)
Spaces Toggle
Hugging Face Spaces(What is Spaces?)
Spaces Toggle
TXYZ.AI(What is TXYZ.AI?)
Related Papers
Recommenders and Search Tools
Link to Influence Flower
Influence Flower(What are Influence Flowers?)
Core recommender toggle
CORE Recommender(What is CORE?)
Author
Venue
Institution
Topic
About arXivLabs
arXivLabs: experimental projects with community collaborators
arXivLabs is a framework that allows collaborators to develop and share new arXiv features directly on our website.
- [ev_3749403d37b1] 2405.07437 (https://arxiv.org/abs/2405.07437, chunk=web_url_0a3e45f0193f#chunk-8). Quote: Both individuals and organizations that work with arXivLabs have embraced and accepted our values of openness, community, excellence, and user data privacy.
- [ev_e1c8df650744] Failure Modes in Deep Research Agents (local://agent/failure-modes, chunk=failure_modes#chunk-1). Quote: Common failure modes include shallow planning, duplicate evidence, unsupported claims, stale memory, over-compression, and judge bias.
- [ev_05b6af6d78eb] Hybrid Memory Design for Research Agents (local://comparison/hybrid-memory-design, chunk=hybrid_memory_design#chunk-1). Quote: A hybrid memory design separates source-of-truth storage from retrieval acceleration.
- [ev_cbe570133ee4] Hybrid Memory Design for Research Agents (local://comparison/hybrid-memory-design, chunk=hybrid_memory_design#chunk-2). Quote: The coordinator can retrieve from the vector index, load full evidence from SQLite, and still preserve citation traceability.
- [ev_6092e4fd2564] Hybrid Memory Design for Research Agents (local://comparison/hybrid-memory-design, chunk=hybrid_memory_design#chunk-1). Quote: SQLite keeps structured tables for runs, tasks, evidence, claims, reports, verification traces, and repair actions.
- [ev_84d3ae0eddd1] SQLite and Vector Retrieval Tradeoffs (local://comparison/sqlite-vector-tradeoffs, chunk=sqlite_vector_tradeoffs#chunk-1). Quote: SQLite and vector retrieval solve different parts of an agent memory problem.
- [ev_65e03c26fe0c] SQLite and Vector Retrieval Tradeoffs (local://comparison/sqlite-vector-tradeoffs, chunk=sqlite_vector_tradeoffs#chunk-2). Quote: A practical DeepResearch Agent often combines both: SQLite stores canonical records and the vector index stores ids for similarity search.

## Limitations

- This run uses a real LLM writer over bounded retrieved evidence.
- 证据未提供具体的提示注入检测算法或基准性能数据，因此方案中的预处理步骤为工程推断。
- 混合内存设计的具体实现（如 SQLite 与向量索引的组合）来自本地资料，未在 NIST 或 OWASP 文档中明确提及。
- 评测指标（如 relevance, accuracy, faithfulness）的量化阈值需根据具体应用场景调整，证据未给出推荐值。
- Some retrieved evidence contains conflict cues; related claims should be stated cautiously.