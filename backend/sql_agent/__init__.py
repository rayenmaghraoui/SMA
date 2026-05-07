"""
Module SQL Agent — exploration de données via langage naturel.

Composants :
    - db.py         : connexion DuckDB, chargement des 3 CSV comme tables
    - validator.py  : validation sécurité (SELECT only, mots-clés interdits, LIMIT)
    - generator.py  : génération SQL depuis une question NL (via LLM DeepSeek)
    - executor.py   : exécution SQL avec timeout
    - intent_router.py : classification d'intention (stratégique vs exploration data)
"""
