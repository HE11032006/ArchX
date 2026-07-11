SYSTEM_PROMPT = {
    "fr": (
        "Tu es un architecte logiciel senior expert en analyse de code et migration technologique. "
        "Tu dois répondre UNIQUEMENT en JSON valide avec la structure demandée. "
        "N'affirme jamais une stack technique, un âge de projet, ou une composition d'équipe "
        "(niveau d'expérience, ratio junior/senior) qui ne sont pas explicitement fournis dans le "
        "contexte ci-dessous — reste sur les métriques et anti-patterns donnés, comme pour les "
        "montants financiers que tu ne dois jamais inventer."
    ),
    "en": (
        "You are a senior software architect expert in code analysis and technology migration. "
        "You must respond ONLY with valid JSON using the requested structure. "
        "Never assert a tech stack, project age, or team composition (experience level, "
        "junior/senior ratio) that is not explicitly provided in the context below — stick to the "
        "given metrics and anti-patterns, the same way you must never invent financial figures."
    ),
}

def build_user_message(language: str, input_data: dict) -> str:
    """Construit le message 'user' à partir d'un bloc `input`."""
    metrics = input_data.get("metrics", {})
    anti_patterns = input_data.get("anti_patterns", [])
    languages = input_data.get("languages", {})
    dependencies = input_data.get("dependencies", {})
    database = input_data.get("database", {})
    tests = input_data.get("tests", {})
    performance = input_data.get("performance", {})
    
    # NOUVEAU : métriques AST multi-langages
    js_analysis = input_data.get("js_analysis", {})
    java_analysis = input_data.get("java_analysis", {})
    dart_analysis = input_data.get("dart_analysis", {})

    if language == "fr":
        # Section langages (déjà existante)
        if languages:
            lang_lines = []
            for lang, info in languages.items():
                frameworks = ", ".join(info.get("frameworks", [])) if info.get("frameworks") else "aucun framework"
                lang_lines.append(f"  - {lang}: {info['file_count']} fichiers, {info['line_count']} lignes (frameworks: {frameworks})")
            multi_lang_section = "\nLANGAGES DÉTECTÉS (multi-langages)\n" + "\n".join(lang_lines) + "\n"
        else:
            multi_lang_section = ""
        
        # NOUVEAU : section AST JavaScript/TypeScript
        if js_analysis and js_analysis.get("files_analyzed", 0) > 0:
            js_lines = [
                f"  - Fichiers analysés : {js_analysis.get('files_analyzed', 0)}",
                f"  - Fonctions détectées : {js_analysis.get('total_functions', 0)}",
                f"  - Classes détectées : {js_analysis.get('total_classes', 0)}",
                f"  - Erreurs de parsing : {js_analysis.get('file_errors', 0)}"
            ]
            js_section = "\nANALYSE JavaScript/TypeScript (AST)\n" + "\n".join(js_lines) + "\n"
        else:
            js_section = ""
        
        # NOUVEAU : section AST Java
        if java_analysis and java_analysis.get("files_analyzed", 0) > 0:
            java_lines = [
                f"  - Fichiers analysés : {java_analysis.get('files_analyzed', 0)}",
                f"  - Méthodes détectées : {java_analysis.get('total_methods', 0)}",
                f"  - Classes détectées : {java_analysis.get('total_classes', 0)}",
                f"  - Erreurs de parsing : {java_analysis.get('file_errors', 0)}"
            ]
            java_section = "\nANALYSE Java (AST)\n" + "\n".join(java_lines) + "\n"
        else:
            java_section = ""
        
        # NOUVEAU : section AST Dart
        if dart_analysis and dart_analysis.get("files_analyzed", 0) > 0:
            dart_lines = [
                f"  - Fichiers analysés : {dart_analysis.get('files_analyzed', 0)}",
                f"  - Fonctions détectées : {dart_analysis.get('total_functions', 0)}",
                f"  - Classes détectées : {dart_analysis.get('total_classes', 0)}",
                f"  - Erreurs de parsing : {dart_analysis.get('file_errors', 0)}"
            ]
            dart_section = "\nANALYSE Dart/Flutter (AST)\n" + "\n".join(dart_lines) + "\n"
        else:
            dart_section = ""
        
        # Section dépendances (existante)
        if dependencies and dependencies.get("has_dependency_files"):
            dep_lines = []
            for lang, info in dependencies.get("languages", {}).items():
                dep_lines.append(f"  - {lang}: {info['count']} dépendances ({info['obsolete_count']} obsolètes)")
            dep_section = "\nDÉPENDANCES\n" + "\n".join(dep_lines) + "\n"
        else:
            dep_section = ""
        
        # Section base de données (existante)
        if database and database.get("has_database"):
            db_lines = [
                f"  - SGBD détectés: {', '.join(database.get('detected_databases', []))}",
                f"  - ORM: {', '.join(database.get('detected_orms', []))}",
                f"  - Nombre de migrations: {database.get('migration_count', 0)}",
                f"  - Complexité estimée: {database.get('complexity', 'non évaluée')}"
            ]
            db_section = "\nBASE DE DONNÉES\n" + "\n".join(db_lines) + "\n"
        else:
            db_section = ""
        
        # Section tests (existante)
        if tests:
            test_lines = [
                f"  - Fichiers de test: {tests.get('total_test_files', 0)}",
                f"  - Fonctions de test: {tests.get('total_test_functions', 0)}",
                f"  - Ratio de tests: {tests.get('test_ratio', 0)}%",
                f"  - Couverture estimée: {tests.get('coverage_estimate', 'non évaluée')}",
                f"  - Frameworks: {', '.join(tests.get('frameworks', []))}"
            ]
            test_section = "\nTESTS\n" + "\n".join(test_lines) + "\n"
        else:
            test_section = ""
        
        # Section performance (existante)
        if performance:
            perf_lines = [
                f"  - Endpoints détectés: {performance.get('endpoints_count', 0)}",
                f"  - Appels externes: {performance.get('external_calls_detected', 0)}",
                f"  - Opérations de cache: {performance.get('cached_operations_detected', 0)}",
                f"  - Opérations asynchrones: {performance.get('async_operations_detected', 0)}",
                f"  - Score de performance: {performance.get('performance_score', 'non évalué')}",
                f"  - Potentiels N+1: {performance.get('potential_n_plus_1_hotspots', 0)}"
            ]
            perf_section = "\nPERFORMANCE\n" + "\n".join(perf_lines) + "\n"
        else:
            perf_section = ""
        
        # Section anti-patterns (existante)
        ap_lines = "\n".join(
            f"  - {a['type']} ({a['severity']}) dans {a['location']}" for a in anti_patterns
        ) or "  - Aucun anti-pattern significatif détecté"
        
        # Section métriques (existante)
        metric_lines = "\n".join(f"  - {k} : {v}" for k, v in metrics.items())
        
        context = input_data.get("sector", input_data.get("repo_path", "projet non spécifié"))
        team = input_data.get("team_size")
        team_line = f"\n- Équipe : {team} développeurs" if team else ""
        stack_bits = [b for b in (input_data.get("language"), input_data.get("database_name")) if b]
        stack_line = f"\n- Stack connue : {', '.join(stack_bits)}" if stack_bits else ""

        return (
            f"CONTEXTE\n- {context}{team_line}{stack_line}\n\n"
            f"MÉTRIQUES CALCULÉES (Python)\n{metric_lines}\n\n"
            f"{multi_lang_section}"
            f"{js_section}"
            f"{java_section}"
            f"{dart_section}"
            f"{dep_section}"
            f"{db_section}"
            f"{test_section}"
            f"{perf_section}"
            f"ANTI-PATTERNS DÉTECTÉS (Python)\n{ap_lines}\n\n"
            f"Analyse ce projet en tenant compte de l'ensemble des langages, "
            f"des métriques AST (JavaScript/TypeScript, Java, Dart), des dépendances, "
            f"de la base de données, des tests et des performances. "
            f"Réponds en JSON avec les champs : "
            f"project_description, analysis, recommendation, phases, risk_assessment."
        )
    
    else:
        # Version anglaise
        # Section langages
        if languages:
            lang_lines = []
            for lang, info in languages.items():
                frameworks = ", ".join(info.get("frameworks", [])) if info.get("frameworks") else "no framework"
                lang_lines.append(f"  - {lang}: {info['file_count']} files, {info['line_count']} lines (frameworks: {frameworks})")
            multi_lang_section = "\nLANGUAGES DETECTED (multi-language)\n" + "\n".join(lang_lines) + "\n"
        else:
            multi_lang_section = ""
        
        # Section AST JS/TS
        if js_analysis and js_analysis.get("files_analyzed", 0) > 0:
            js_lines = [
                f"  - Files analyzed: {js_analysis.get('files_analyzed', 0)}",
                f"  - Functions detected: {js_analysis.get('total_functions', 0)}",
                f"  - Classes detected: {js_analysis.get('total_classes', 0)}",
                f"  - Parse errors: {js_analysis.get('file_errors', 0)}"
            ]
            js_section = "\nJavaScript/TypeScript ANALYSIS (AST)\n" + "\n".join(js_lines) + "\n"
        else:
            js_section = ""
        
        # Section AST Java
        if java_analysis and java_analysis.get("files_analyzed", 0) > 0:
            java_lines = [
                f"  - Files analyzed: {java_analysis.get('files_analyzed', 0)}",
                f"  - Methods detected: {java_analysis.get('total_methods', 0)}",
                f"  - Classes detected: {java_analysis.get('total_classes', 0)}",
                f"  - Parse errors: {java_analysis.get('file_errors', 0)}"
            ]
            java_section = "\nJava ANALYSIS (AST)\n" + "\n".join(java_lines) + "\n"
        else:
            java_section = ""
        
        # Section AST Dart
        if dart_analysis and dart_analysis.get("files_analyzed", 0) > 0:
            dart_lines = [
                f"  - Files analyzed: {dart_analysis.get('files_analyzed', 0)}",
                f"  - Functions detected: {dart_analysis.get('total_functions', 0)}",
                f"  - Classes detected: {dart_analysis.get('total_classes', 0)}",
                f"  - Parse errors: {dart_analysis.get('file_errors', 0)}"
            ]
            dart_section = "\nDart/Flutter ANALYSIS (AST)\n" + "\n".join(dart_lines) + "\n"
        else:
            dart_section = ""
        
        # Section dépendances
        if dependencies and dependencies.get("has_dependency_files"):
            dep_lines = []
            for lang, info in dependencies.get("languages", {}).items():
                dep_lines.append(f"  - {lang}: {info['count']} dependencies ({info['obsolete_count']} obsolete)")
            dep_section = "\nDEPENDENCIES\n" + "\n".join(dep_lines) + "\n"
        else:
            dep_section = ""
        
        # Section base de données
        if database and database.get("has_database"):
            db_lines = [
                f"  - DB detected: {', '.join(database.get('detected_databases', []))}",
                f"  - ORM: {', '.join(database.get('detected_orms', []))}",
                f"  - Migration count: {database.get('migration_count', 0)}",
                f"  - Estimated complexity: {database.get('complexity', 'not evaluated')}"
            ]
            db_section = "\nDATABASE\n" + "\n".join(db_lines) + "\n"
        else:
            db_section = ""
        
        # Section tests
        if tests:
            test_lines = [
                f"  - Test files: {tests.get('total_test_files', 0)}",
                f"  - Test functions: {tests.get('total_test_functions', 0)}",
                f"  - Test ratio: {tests.get('test_ratio', 0)}%",
                f"  - Coverage estimate: {tests.get('coverage_estimate', 'not evaluated')}",
                f"  - Frameworks: {', '.join(tests.get('frameworks', []))}"
            ]
            test_section = "\nTESTS\n" + "\n".join(test_lines) + "\n"
        else:
            test_section = ""
        
        # Section performance
        if performance:
            perf_lines = [
                f"  - Endpoints detected: {performance.get('endpoints_count', 0)}",
                f"  - External calls: {performance.get('external_calls_detected', 0)}",
                f"  - Cache operations: {performance.get('cached_operations_detected', 0)}",
                f"  - Async operations: {performance.get('async_operations_detected', 0)}",
                f"  - Performance score: {performance.get('performance_score', 'not evaluated')}",
                f"  - Potential N+1 hotspots: {performance.get('potential_n_plus_1_hotspots', 0)}"
            ]
            perf_section = "\nPERFORMANCE\n" + "\n".join(perf_lines) + "\n"
        else:
            perf_section = ""
        
        ap_lines = "\n".join(
            f"  - {a['type']} ({a['severity']}) in {a['location']}" for a in anti_patterns
        ) or "  - No significant anti-pattern detected"
        
        metric_lines = "\n".join(f"  - {k}: {v}" for k, v in metrics.items())
        context = input_data.get("sector", input_data.get("repo_path", "unspecified project"))
        team = input_data.get("team_size")
        team_line = f"\n- Team: {team} developers" if team else ""
        stack_bits = [b for b in (input_data.get("language"), input_data.get("database_name")) if b]
        stack_line = f"\n- Known stack: {', '.join(stack_bits)}" if stack_bits else ""

        return (
            f"CONTEXT\n- {context}{team_line}{stack_line}\n\n"
            f"COMPUTED METRICS (Python)\n{metric_lines}\n\n"
            f"{multi_lang_section}"
            f"{js_section}"
            f"{java_section}"
            f"{dart_section}"
            f"{dep_section}"
            f"{db_section}"
            f"{test_section}"
            f"{perf_section}"
            f"DETECTED ANTI-PATTERNS (Python)\n{ap_lines}\n\n"
            f"Analyze this project considering all detected languages, "
            f"AST metrics (JavaScript/TypeScript, Java, Dart), dependencies, "
            f"database, tests, and performance. "
            f"Answer in JSON with the fields: "
            f"project_description, analysis, recommendation, phases, risk_assessment."
        )