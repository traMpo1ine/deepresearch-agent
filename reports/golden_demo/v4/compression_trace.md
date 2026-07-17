# Showcase Compression Trace

Question: 请基于下面三份公开资料，为一个可审计的 DeepResearch Agent 设计工程方案：说明为什么要分别评测检索与生成、如何保留引用溯源，以及如何把提示注入作为不可信输入处理。请区分资料明确支持的结论与工程推断，并给出可以落地的最小检查清单。
https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
https://genai.owasp.org/llm-top-10/
https://arxiv.org/abs/2405.07437
Original chars: `11352`
Compressed chars: `9037`
Compression ratio: `0.796`
Selected sentences: `29`

## Selected Sentences

### Sentence 1

SQLite and vector retrieval solve different parts of an agent memory problem.

Evidence: `ev_d88e54368042`
Source: `sqlite_vector_tradeoffs`
Preserved quote: `true`
Score: `1.255`

### Sentence 2

Both individuals and organizations that work with arXivLabs have embraced and accepted our values of openness, community, excellence, and user data privacy.

Evidence: `ev_0d2b628a3574`
Source: `web_url_0a3e45f0193f`
Preserved quote: `true`
Score: `1.158`

### Sentence 3

Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile | NIST
Skip to main content
An official website of the United States government
Here’s how you know
Here’s how you know
Official websites use .gov
A .gov website belongs to an official government organization in the United States.

Evidence: `ev_1b56c7fd7942`
Source: `web_url_017252c14514`
Preserved quote: `true`
Score: `1.105`

### Sentence 4

Numerous studies and real-world applications are leveraging its ability to enhance generative models through external information retrieval.

Evidence: `ev_60c77e25a827`
Source: `web_url_0a3e45f0193f`
Preserved quote: `true`
Score: `1.101`

### Sentence 5

GETTING STARTED
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
AIBOM Generator
GOVERNANCE CHECKLIST
Threat Intelligence
AGENTIC APP SECURITY
Secure AI Adoption
AI Red Teaming
Data Security
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
TOP 10 FOR GEN AI
2025 Top 10 Risk & Mitigations for LLMs and Gen AI Apps
Expore the latest Top 10 risks, vulnerabilities and mitigations for developing and securing generative AI and large language model applications across the development, deployment and management lifecycle.

Evidence: `ev_81275f940e75`
Source: `web_url_10793bb5a69b`
Preserved quote: `true`
Score: `1.099`

### Sentence 6

The coordinator can retrieve from the vector index, load full evidence from SQLite, and still preserve citation traceability.

Evidence: `ev_ff55200b6243`
Source: `hybrid_memory_design`
Preserved quote: `true`
Score: `1.088`

### Sentence 7

To better understand these challenges, we conduct A Unified Evaluation Process of RAG (Auepora) and aim to provide a comprehensive overview of the evaluation and benchmarks of RAG systems.

Evidence: `ev_2834b9990d17`
Source: `web_url_0a3e45f0193f`
Preserved quote: `true`
Score: `1.086`

### Sentence 8

A practical DeepResearch Agent often combines both: SQLite stores canonical records and the vector index stores ids for similarity search.

Evidence: `ev_8436d4652282`
Source: `sqlite_vector_tradeoffs`
Preserved quote: `true`
Score: `1.080`

### Sentence 9

Secure .gov websites use HTTPS
A lock (
) or https:// means you’ve safely connected to the .gov website.

Evidence: `ev_a40d6ea519d1`
Source: `web_url_017252c14514`
Preserved quote: `true`
Score: `1.000`

### Sentence 10

https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
Menu
PUBLICATIONS
Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile
Published
July 26, 2024
Author(s)
Chloe Autio, Reva Schwartz, Jesse Dunietz, Shomik Jain, Martin Stanley, Elham Tabassi, Patrick Hall, Kamie Roberts
Abstract
This document is a cross-sectoral profile of and companion resource for the AI Risk Management Framework (AI RMF 1.0) for Generative AI, pursuant to President Biden's Executive Order (EO) 14110 on Safe, Secure, and Trustworthy Artificial Intelligence.

Evidence: `ev_61bd81994410`
Source: `web_url_017252c14514`
Preserved quote: `true`
Score: `1.000`

### Sentence 11

The AI RMF was released in January 2023, and is intended for voluntary use and to improve the ability of organizations to incorporate trustworthiness considerations into the design, development, use, and evaluation of AI products, services, and systems.

Evidence: `ev_647afe20e1e9`
Source: `web_url_017252c14514`
Preserved quote: `true`
Score: `1.000`

### Sentence 12

Citation
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

Evidence: `ev_eeb3c3048631`
Source: `web_url_017252c14514`
Preserved quote: `true`
Score: `1.000`

### Sentence 13

, Schwartz, R.

Evidence: `ev_37f72fdacadf`
Source: `web_url_017252c14514`
Preserved quote: `true`
Score: `1.000`

### Sentence 14

(2024),
Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile, NIST Trustworthy and Responsible AI, National Institute of Standards and Technology, Gaithersburg, MD, [online], https://doi.org/10.6028/NIST.AI.600-1, https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=958388 (Accessed July 16, 2026)
Additional citation formats
Google Scholar
DOI
BibTeX
RIS
Issues
If you have any questions about this publication or are having problems accessing it, please contact [email protected].

Evidence: `ev_2c0e61a9ddb7`
Source: `web_url_017252c14514`
Preserved quote: `true`
Score: `1.000`

### Sentence 15

Created July 26, 2024, Updated April 8, 2026
Was this page helpful?

Evidence: `ev_2ae0e6fd9106`
Source: `web_url_017252c14514`
Preserved quote: `true`
Score: `1.000`

### Sentence 16

LLMRisks Archive - OWASP Gen AI Security Project
Skip to content
Join us in London, 6/2 – 6/4 InfoSecurity Europe – OWASP GenAI and Agentic Security Summit
|
Register Now!

Evidence: `ev_de56a8cccf3e`
Source: `web_url_10793bb5a69b`
Preserved quote: `true`
Score: `1.000`

### Sentence 17

Read the OWASP Top 10 for LLMs 2023-24
Download
LLM01:2025 Prompt Injection
A Prompt Injection Vulnerability occurs when user prompts alter the...

Evidence: `ev_54c27cb4e2ac`
Source: `web_url_10793bb5a69b`
Preserved quote: `true`
Score: `1.000`

### Sentence 18

Read More
LLM04:2025 Data and Model Poisoning
Data poisoning occurs when pre-training, fine-tuning, or embedding data is...

Evidence: `ev_d1d4dc2de348`
Source: `web_url_10793bb5a69b`
Preserved quote: `true`
Score: `1.000`

### Sentence 19

Read More
LLM07:2025 System Prompt Leakage
The system prompt leakage vulnerability in LLMs refers to the...

Evidence: `ev_d9ca0f74908a`
Source: `web_url_10793bb5a69b`
Preserved quote: `true`
Score: `1.000`

### Sentence 20

Read More
LLM10:2025 Unbounded Consumption
Unbounded Consumption refers to the process where a Large Language...

Evidence: `ev_d4a4f763a167`
Source: `web_url_10793bb5a69b`
Preserved quote: `true`
Score: `1.000`

### Sentence 21

Read More
Document Versions and Translations
April 11, 2024
LLM Top 10 for LLMs 2024
May 4, 2024
OWASP Top 10 for LLM Overview Presentation
May 7, 2024
LLM Top 10 for LLMs 2024 – Chinese
Top 10 2025 de riesgos y mitigaciones para LLMs y aplicaciones de IA Generativa
View »
March 12, 2025
OWASP Top 10 para Aplicações de LLM e IA Generativa (2025)
View »
March 12, 2025
OWASP大型語言模型及生成式 AI 十大風險（2025)
View »
March 12, 2025
2025 में LLM Applications के लि ए OWASP के शी र्ष 10
View »
July 22, 2025
OWASP Τοπ-10 για Εφαρμογές LLM 2025
View »
July 22, 2025
LLM 애플리케이션을 위한 OWASP Top 10 2025
View »
July 22, 2025
OWASP Top 10 для LLM и генеративного ИИ (2025)
View »
March 12, 2025
OWASP大型语言模型与生成式AI十大风险（2025）
View »
March 12, 2025
die OWASP Top 10 für LLM & Generative KI (2025)
View »
March 12, 2025
大規模言語モデル（LLM）アプリケーションに関するOWASP Top 10
View »
July 22, 2025
Scroll to Top
LLM10:2025 Unbounded Consumption
Loading Comments...

Evidence: `ev_308b56eece1c`
Source: `web_url_10793bb5a69b`
Preserved quote: `true`
Score: `1.000`

### Sentence 22

[2405.07437] Evaluation of Retrieval-Augmented Generation: A Survey
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

Evidence: `ev_c6c2f2f6b649`
Source: `web_url_0a3e45f0193f`
Preserved quote: `true`
Score: `1.000`

### Sentence 23

Specifically, we examine and compare several quantifiable metrics of the Retrieval and Generation components, such as relevance, accuracy, and faithfulness, within the current RAG benchmarks, encompassing the possible output and ground truth pairs.

Evidence: `ev_5594ca4a6fb1`
Source: `web_url_0a3e45f0193f`
Preserved quote: `true`
Score: `1.000`

### Sentence 24

Subjects:
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

Evidence: `ev_86848fa3db1b`
Source: `web_url_0a3e45f0193f`
Preserved quote: `true`
Score: `1.000`

### Sentence 25

BibTeX formatted citation
×
loading...

Evidence: `ev_96aff80d5820`
Source: `web_url_0a3e45f0193f`
Preserved quote: `true`
Score: `1.000`

### Sentence 26

Data provided by:
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

Evidence: `ev_102e921822fd`
Source: `web_url_0a3e45f0193f`
Preserved quote: `true`
Score: `1.000`

### Sentence 27

Common failure modes include shallow planning, duplicate evidence, unsupported claims, stale memory, over-compression, and judge bias.

Evidence: `ev_efd89b5ff580`
Source: `failure_modes`
Preserved quote: `true`
Score: `1.000`

### Sentence 28

A hybrid memory design separates source-of-truth storage from retrieval acceleration.

Evidence: `ev_661721ef9049`
Source: `hybrid_memory_design`
Preserved quote: `true`
Score: `1.000`

### Sentence 29

SQLite keeps structured tables for runs, tasks, evidence, claims, reports, verification traces, and repair actions.

Evidence: `ev_91531f6879f4`
Source: `hybrid_memory_design`
Preserved quote: `true`
Score: `1.000`
