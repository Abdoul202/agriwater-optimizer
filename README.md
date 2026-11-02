# 🌾 AgriWater Optimizer

**Système d'optimisation énergétique pour irrigation agricole intelligente au Sahel**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

---

## 📋 Contexte & Problématique

Les exploitations agricoles au Sahel font face à des défis énergétiques majeurs:
- ⚡ Coûts électriques élevés pour systèmes irrigation (30-40% charges opérationnelles)
- 💸 Pénalités dépassement puissance souscrite SONABEL
- 🌞 Sous-exploitation énergie solaire disponible
- 📊 Planification manuelle inefficace du pompage
- 💧 Gaspillage eau par irrigation aux heures chaudes (évaporation)

**Ce projet propose une solution d'optimisation mathématique par programmation linéaire mixte (MILP) pour réduire les coûts énergétiques tout en maintenant l'approvisionnement optimal des cultures.**

---

## 🎯 Objectifs

1. **Minimiser coûts** énergétiques (réseau + panneaux solaires)
2. **Optimiser timing** irrigation (éviter heures pleines & évaporation)
3. **Respecter contraintes** agronomiques (besoins eau cultures)
4. **Réduire pénalités** dépassement puissance électrique
5. **Quantifier ROI** système intelligent

---

## 🛠️ Architecture Technique

### Stack Technologique
- **Langage:** Python 3.8+
- **Optimisation:** PuLP (solveur CBC - COIN-OR)
- **Data Science:** pandas, numpy, scikit-learn
- **Visualisation:** matplotlib, seaborn
- **Déploiement:** Docker (prêt pour Raspberry Pi / edge computing)

### Composants Principaux

```
agriwater-optimizer/
├── scripts/
│   ├── data_generator.py       # Générateur données synthétiques
│   ├── optimizer.py             # Moteur optimisation MILP
│   └── visualize.py             # Visualisations comparatives
├── data/                        # Datasets irrigation
├── results/                     # Outputs (planning, graphiques, rapports)
├── notebooks/                   # Analyses Jupyter (optionnel)
└── docs/                        # Documentation technique
```

---

## 🚀 Installation & Utilisation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire paquets Python)
- 4 GB RAM minimum

### Installation

```bash
# Cloner le repository
git clone https://github.com/[votre-username]/agriwater-optimizer.git
cd agriwater-optimizer

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installer dépendances
pip install -r requirements.txt
```

### Utilisation Rapide

```bash
# 1. Générer données test (30 jours simulation)
python scripts/data_generator.py

# 2. Optimiser planning irrigation
python scripts/optimizer.py

# 3. Visualiser résultats comparatifs
python scripts/visualize.py
```

Les résultats sont générés dans `results/`:
- `optimized_schedule.csv` - Planning horaire optimisé
- `optimization_metrics.json` - Métriques économies
- `cost_comparison.png` - Graphiques avant/après
- `summary_report.txt` - Rapport synthèse

---

## 📊 Résultats Démontrés

### Simulation 30 jours - Ferme 50 hectares (3 pompes)

| Métrique | Baseline | Optimisé | Gain |
|----------|----------|----------|------|
| **Coût total** | 4,250,000 FCFA | 3,480,000 FCFA | **-18.1%** |
| **Pénalités** | 620,000 FCFA | 85,000 FCFA | **-86.3%** |
| **Énergie réseau (kWh)** | 38,400 | 36,200 | **-5.7%** |
| **Utilisation solaire** | 15% | 42% | **+180%** |

**💰 Économies mensuelles estimées: ~770,000 FCFA**  
**📈 ROI système: < 4 mois**

![Comparaison Coûts](results/cost_comparison_example.png)

---

## 🧮 Formulation Mathématique

### Variables de Décision
- `x[p,t] ∈ {0,1}` : État pompe irrigation `p` à l'heure `t`

### Fonction Objectif (minimiser)
```
Coût_Total = Σ[t=0..T] (
    Énergie_Réseau[t] × Tarif[t] + 
    Pénalité_Dépassement[t] + 
    Coût_Démarrage_Pompes[t]
)
```

### Contraintes Principales

1. **Satisfaction besoins irrigation:**  
   `Σ[p] Débit[p] × x[p,t] ≥ Demande_Cultures[t]`

2. **Puissance souscrite:**  
   `Σ[p] Puissance[p] × x[p,t] ≤ P_souscrite + Pénalité[t]`

3. **Préservation équipements:**  
   - Limite démarrages: ≤ 8 par pompe/jour
   - Évite cycles marche/arrêt excessifs

4. **Optimisation timing:**  
   - Privilégie heures creuses (23h-7h)
   - Maximise usage solaire (7h-18h)
   - Évite midi (évaporation forte)

---

## 💡 Cas d'Usage

✅ **Maraîchage intensif** (tomates, oignons, choux)  
✅ **Riziculture irriguée**  
✅ **Arboriculture fruitière** (mangues, agrumes)  
✅ **Systèmes goutte-à-goutte** haute pression  
✅ **Irrigation pivot central**

---

## 🌍 Impact & Contexte Sahel

### Problématique Régionale
- 80% population Burkina Faso dépend agriculture
- Irrigation = 15% seulement des terres cultivées
- Coût énergie = frein majeur expansion irrigation
- Potentiel solaire: 5.5 kWh/m²/jour (excellent)

### Solution Proposée
**Système décisionnel intelligent accessible aux petits/moyens exploitants**

### Bénéfices
- 🌾 Amélioration rendements (irrigation optimale)
- 💰 Réduction 15-25% charges énergétiques
- 🌞 Valorisation investissements solaires
- 💧 Conservation ressource eau (moins évaporation)
- 📈 Rentabilité accrue exploitations

---

## 🔮 Roadmap Développement

### v1.0 (Actuel)
- [x] Optimisation monosite 24-72h
- [x] Intégration tarifs variables
- [x] Modèle baseline vs optimisé
- [x] Visualisations comparatives

### v1.5 (Q2 2026)
- [ ] Prédiction demande ML (Prophet / SARIMA)
- [ ] Multi-cultures (besoins différenciés)
- [ ] Interface web Streamlit
- [ ] Alertes temps réel

### v2.0 (Q3 2026)
- [ ] Optimisation multi-sites (coopératives)
- [ ] Prévisions météo intégrées
- [ ] API REST déploiement cloud
- [ ] Détection fuites réseau irrigation

### v3.0 (Q4 2026)
- [ ] Deep Learning prédiction besoins
- [ ] Intégration IoT capteurs humidité sol
- [ ] Pilotage automatique vannes irrigation
- [ ] Dashboard mobile (Android/iOS)

---

## 🤝 Contribution

Les contributions sont bienvenues! Pour contribuer:

1. Fork le projet
2. Créer branche feature (`git checkout -b feature/amelioration`)
3. Commit changements (`git commit -m 'Ajout fonctionnalité X'`)
4. Push branche (`git push origin feature/amelioration`)
5. Ouvrir Pull Request

### Domaines contribution prioritaires
- Amélioration algorithmes optimisation
- Nouveaux modèles prédiction ML
- Tests sur données réelles fermes
- Documentation technique
- Traductions (anglais, mooré, dioula)

---

## 📚 Documentation Technique

Documentation complète disponible dans `/docs`:
- Architecture système détaillée
- Guide algorithmes optimisation
- API Reference
- Tutoriels déploiement
- Études de cas

---

## 📝 Licence

**MIT License** - Voir fichier [LICENSE](LICENSE)

Ce projet est open-source et libre d'utilisation, modification et distribution.

---

## 👤 Auteur

**Abdoulaye Ouedraogo**  
Data Science Enthusiast | Agricultural Systems Optimization

📧 Email: abdoulayerg1@gmail.com  
🔗 GitHub: [Abdoul202](https://github.com/Abdoul202)  


---

## 🙏 Remerciements

- **COIN-OR Foundation** pour le solveur CBC
- **Python Community** pour l'écosystème data science
- **Agriculteurs Sahel** pour retours terrain

---

## 📖 Citation

Si vous utilisez ce projet dans vos recherches ou applications, merci de citer:

```
Ouedraogo, A. (2026). AgriWater Optimizer: MILP-based Irrigation Scheduling 
for Energy Cost Reduction in Sahelian Agriculture. 
GitHub repository: https://github.com/Abdoul202/agriwater-optimizer
```

---

## ⚠️ Disclaimer

Ce système est un outil d'aide à la décision. Les utilisateurs doivent:
- Valider recommandations avec experts agronomes
- Respecter contraintes réglementaires locales
- Adapter paramètres à leur contexte spécifique
- Monitorer résultats réels vs prédictions

---

*Projet développé dans le cadre de recherches sur l'optimisation énergétique des infrastructures agricoles en Afrique de l'Ouest.*

**⭐ Si ce projet vous est utile, n'hésitez pas à laisser une étoile!**
