# Minicode - Agent Autonome Local (Ollama & Python)

Minicode (en référence à Opencode) est un agent LLM autonome développé de zéro en Python.
L'objectif de ce projet est de comprendre en profondeur le fonctionnement des agents IA (Tool Calling, boucle ReAct, mémoire) en construisant tout "from scratch" avant de passer éventuellement à des frameworks plus lourds (LangGraph, CrewAI). Le projet s'appuie sur l'API locale d'**Ollama** (idéalement avec un modèle doué pour l'appel d'outils comme Qwen 2.5 / 3.5)

Je le met en public car j'ai tenté de le rendre assez modulable pour un usage par quelqu'un d'autre, et qu'au fur et à mesure de l'avancement de la roadmap, cet agent devrait être capable d'apporter une aide pour ceux ayant besoin d'un mini agent permettant des tâches simples sans avoir à payer ou brûler des tokens chez d'autres services.

## Fonctionnalités actuelles

- **Communication API directe** : Appels HTTP bruts à l'API locale d'Ollama.
- **Introspection des outils** : Génération dynamique du schéma JSON des outils (le LLM comprend automatiquement les fonctions Python disponibles grâce à leurs *docstrings*).
- **Boucle ReAct Autonome** : L'agent est capable d'enchaîner plusieurs appels d'outils (Tool Calling) en autonomie jusqu'à la résolution de la tâche.
- **Outils intégrés** :
  - `search_web` : Recherche internet rapide via DuckDuckGo.
  - `fetch_url` : Scraping et nettoyage complet d'une page web (BeautifulSoup).
  - `read_file` : Lecture sécurisée de fichiers locaux.
  - `calculate` : Calculs mathématiques.
  - `get_weather` : Recherche de la météo d'une ville ou région donnée.
  - `search_wikipedia` : Recherche sur Wikipédia d'un sujet ou concept.
  - `get_time` : Outil permettant à l'agent de savoir quelle heure il est en se basant sur le système.

## 🚀 Installation
1. **Prérequis** : Assurez-vous d'avoir [Ollama](https://ollama.com/) installé et lancé sur votre machine avec un modèle compatible (ex: `qwen2.5:14b` ou `qwen3.5:9b`).
   ```bash
   ollama pull qwen2.5:14b
    ```
2. **Cloner le dépôt** :
    ```bash
    git clone [https://github.com/lezardsc/minicode.git](https://github.com/lezardsc/minicode.git)
    cd minicode
    ```
3. **Installer les dépendances** :
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

## Utilisation
Lancez simplement le script principal pour interagir avec l'agent dans votre terminal:
    ```bash
    python3 main.py
    ```


## ROADMAP
Ce projet est conçu de manière itérative, voici les étapes approximatives de développement :

### Phase 1 - les fondations
- Appel HTTP brut à Ollama ✅
- Historique conversationnel maintenu côté client ✅
- Tool calling à un outil ✅
- Multi-tools avec paramètres + génération dynamique du schéma par introspection ✅

### Phase 2 - L'agent autonome
- System prompt ✅
- Boucle ReAct: enchaîner plusieurs tool calls jusqu'à la réponse finale ✅
- Deeper Internet search ✅
- Maîtrise du mode thinking: comprendre, exploiter ou désactiver le \<think\> de Qwen3.5 ✅
- Streaming des réponses: afficher les tokens au fur et à mesure (ergonomie) ✅
- Arguments pour charger un modèle, un system prompt, une URL, un nombre maximum d'itérations ✅
- Arguments pour désactiver le mode thinking ✅

### Phase 3 - Montée de niveau
- Migration vers le SDKOpenAI
- Persistance des conversations
- Gestion du contexte qui grandit: troncature, résumé ou archivage des vieux tours pour ne pas exploser la fenêtre
- Mémoire long terme avec embeddings
- Multimodalité - images
- Audio (speech-to-text)

### Phase 4 - Framework d'agents
- Découverte d'un framework (entre LangGraph, CrewAI ou smolagents)
- Réimplémenter mon agent actuel avec le framework
- Comparer

### Phase 5 - Multi-agents
- Premier système à deux agents
- Pattern hiérarchique (supervisor/worker)
- Pattern débat/consensus
- Pattern parallèle
- Communication structurée
- Mini-projet personnel et fonctionnel pour tester

### Phase 6 - Sujets avancés
- MCP
- Observabilité et logging
- Evaluation des agents
- Robustesse et garde-fous
- Etude de cas: Code source d'OpenCode
- Coût et optimisation
- Vidéo
- Code execution sandboxé, tool qui exécute du code dans un environnement isolé.

### Phase 7 - Projets d'application
- Agent documentation: prend un repo, le parcourt, génère un README ou de la doc pour chaque module.
- Agent test runner: analyse un code, génère des tests, les exécute, itère sur les échecs.
- Agent refactoriseur: refactorise un code en justifiant chaque changement en commentaire/fichier annexe
- Agent traducteur de code: Python -> Rust, JS -> Go, etc.



Ce projet est à but éducatif. N'hésitez pas à ouvrir une issue ou proposer une PR si vous souhaitez échanger sur l'architecture !