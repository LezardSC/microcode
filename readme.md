ROADMAP:

Phase 1 - les fondations
- Appel HTTP brut à Ollama ✅
- Historique conversationnel maintenu côté client ✅
- Tool calling à un outil ✅
- Multi-tools avec paramètres + génération dynamique du schéma par introspection ✅

Phase 2 - L'agent autonome
- System prompt ✅
- Boucle ReAct: enchaîner plusieurs tool calls jusqu'à la réponse finale ✅
- Deeper Internet search
- Maîtrise du mode thinking: comprendre, exploiter ou désactiver le <think> de Qwen3.5
- Gestion du contexte qui grandit: troncature, résumé ou archivage des vieux tours pour ne pas exploser la fenêtre
- Streaming des réponses: afficher les tokens au fur et à mesure (ergonomie)
- Multimodalité - images

Phase 3 - Montée de niveau
- Migration vers le SDKOpenAI
- Persistance des conversations
- Mémoire long terme avec embeddings
- Audio (speech-to-text)

Phase 4 - Framework d'agents
- Découverte d'un framework (entre LangGraph, CrewAI ou smolagents)
- Réimplémenter mon agent actuel avec le framework
- Comparer

Phase 5 - Multi-agents
- Premier système à deux agents
- Pattern hiérarchique (supervisor/worker)
- Pattern débat/consensus
- Pattern parallèle
- Communication structurée
- Mini-projet personnel et fonctionnel pour tester

Phase 6 - Sujets avancés
- MCP
- Observabilité et logging
- Evaluation des agents
- Robustesse et garde-fous
- Etude de cas: Code source d'OpenCode
- Coût et optimisation
- Vidéo
- Code execution sandboxé, tool qui exécute du code dans un environnement isolé.

Phase 7 - Projets d'application
- Agent documentation: prend un repo, le parcourt, génère un README ou de la doc pour chaque module.
- Agent test runner: analyse un code, génère des tests, les exécute, itère sur les échecs.
- Agent refactoriseur: refactorise un code en justifiant chaque changement en commentaire/fichier annexe
- Agent traducteur de code: Python -> Rust, JS -> Go, etc.