import os
import random
import subprocess
import time

FILENAME = "dummy_metrics_log.txt"

# Liste de messages de commits réalistes en anglais, sans émojis.
# Contient intentionnellement les mots "fix" et "debug" pour déclencher les hotspots.
COMMIT_MESSAGES = [
    "Update dependency versions for security vulnerabilities",
    "Refactor module initialization sequence",
    "Improve performance of data parsing step",
    "fix null pointer exception in collector module",
    "Add logging for missing configuration files",
    "debug unexpected timeout in API requests",
    "Clean up unused variables and dead code",
    "fix incorrect logic in coverage estimation",
    "Optimize memory usage during large repo analysis",
    "Update documentation for setup instructions",
    "debug race condition in parallel processing",
    "Fix typo in variable naming convention",
    "Add unit tests for edge cases in parser",
    "fix memory leak when handling large files",
    "Adjust thresholds for complexity calculation",
    "Update database schema for new metrics",
    "debug edge case with recursive symlinks",
    "fix crash when parsing empty files"
]

def run_cmd(cmd):
    # Exécute une commande shell
    subprocess.run(cmd, shell=True, check=True)

def main():
    print("Démarrage du script de génération de commits...")
    
    # 1. Création du fichier et premier ajout (comme demandé : ajouter avant de modifier)
    with open(FILENAME, "w") as f:
        f.write("Initial tracking log\n")
    
    run_cmd(f"git add {FILENAME}")
    run_cmd('git commit -m "Add initial metrics tracking log"')
    print("Fichier initial créé et commité.")
    
    # 2. Boucle des 100 commits
    for i in range(1, 101):
        with open(FILENAME, "a") as f:
            f.write(f"Log entry {i} at {time.time()}\n")
        
        # Choix aléatoire d'un message
        msg = random.choice(COMMIT_MESSAGES)
        
        run_cmd(f"git add {FILENAME}")
        run_cmd(f'git commit -m "{msg}"')
        
        if i % 10 == 0:
            print(f"{i}/100 commits générés...")

    # 3. Nettoyage (optionnel, pour ne pas laisser de fichier inutile)
    if os.path.exists(FILENAME):
        os.remove(FILENAME)
        run_cmd(f"git add {FILENAME}")
        run_cmd('git commit -m "Clean up temporary tracking log"')
    
    print("Terminé ! 100+ commits ont été ajoutés à l'historique du projet.")

if __name__ == "__main__":
    main()
