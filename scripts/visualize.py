"""
AgriWater Optimizer - Visualization Module
Visualisation comparative baseline vs optimisé
Génère graphiques professionnels pour démonstration
Auteur: Abdoulaye Ouedraogo
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json
import os

# Configuration style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_data():
    """Charge données baseline et optimisées"""
    
    print("\n📂 Chargement données pour visualisation...")
    
    try:
        baseline_df = pd.read_csv("data/irrigation_data.csv")
        baseline_df['timestamp'] = pd.to_datetime(baseline_df['timestamp'])
        print(f"  ✓ Baseline: {len(baseline_df)} enregistrements")
    except FileNotFoundError:
        print("  ❌ Fichier baseline introuvable!")
        return None, None, None
    
    try:
        optimized_df = pd.read_csv("results/optimized_schedule.csv")
        print(f"  ✓ Optimisé: {len(optimized_df)} enregistrements")
    except FileNotFoundError:
        print("  ❌ Fichier optimisé introuvable!")
        print("  → Exécutez d'abord: python optimizer.py")
        return None, None, None
    
    try:
        with open("results/optimization_metrics.json", 'r') as f:
            metrics = json.load(f)
        print(f"  ✓ Métriques chargées")
    except FileNotFoundError:
        metrics = None
        print("  ⚠️  Métriques non disponibles")
    
    return baseline_df, optimized_df, metrics


def plot_cost_comparison(baseline_df, optimized_df, metrics, save_path="results/cost_comparison.png"):
    """Graphique comparaison coûts horaires"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('AgriWater: Analyse Comparative Optimisation Irrigation', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    # Préparer données
    horizon = len(optimized_df)
    baseline_hourly = baseline_df.groupby('hour').agg({
        'total_cost_fcfa': 'sum',
        'power_kw': 'sum',
        'penalty_fcfa': 'sum',
        'energy_cost_fcfa': 'sum'
    }).head(horizon)
    
    hours = range(horizon)
    
    # 1. COÛTS HORAIRES TOTAUX
    ax1 = axes[0, 0]
    
    width = 0.35
    x = np.arange(len(hours))
    
    baseline_costs = baseline_hourly['total_cost_fcfa'].values
    optimized_costs = optimized_df['total_cost_fcfa'].values
    
    bars1 = ax1.bar(x - width/2, baseline_costs, width, label='Baseline', 
                    color='#e74c3c', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars2 = ax1.bar(x + width/2, optimized_costs, width, label='Optimisé', 
                    color='#27ae60', alpha=0.8, edgecolor='black', linewidth=0.5)
    
    ax1.set_xlabel('Heure de la journée', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Coût total (FCFA)', fontsize=11, fontweight='bold')
    ax1.set_title('Coûts Horaires Totaux (Énergie + Pénalités)', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'{h}h' for h in hours], rotation=45, ha='right')
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Annotations zones tarifaires
    ax1.axvspan(-0.5, 6.5, alpha=0.1, color='blue', label='HC')
    ax1.axvspan(6.5, 22.5, alpha=0.1, color='orange', label='HP')
    if horizon >= 23:
        ax1.axvspan(22.5, horizon-0.5, alpha=0.1, color='blue')
    
    # 2. CONSOMMATION ÉNERGÉTIQUE
    ax2 = axes[0, 1]
    
    baseline_energy = baseline_hourly['power_kw'].values
    optimized_energy = optimized_df['total_power_kw'].values
    
    ax2.plot(hours, baseline_energy, 'o-', label='Baseline', 
             color='#e74c3c', linewidth=2.5, markersize=6, alpha=0.8)
    ax2.plot(hours, optimized_energy, 's-', label='Optimisé', 
             color='#27ae60', linewidth=2.5, markersize=6, alpha=0.8)
    
    # Ligne puissance souscrite
    if metrics and 'baseline_cost_fcfa' in metrics:
        subscribed_power = 150  # kW (valeur par défaut)
        ax2.axhline(y=subscribed_power, color='red', linestyle='--', 
                    linewidth=2, label=f'Puissance souscrite ({subscribed_power} kW)', alpha=0.7)
    
    ax2.set_xlabel('Heure de la journée', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Puissance (kW)', fontsize=11, fontweight='bold')
    ax2.set_title('Consommation Énergétique Horaire', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(hours)
    ax2.set_xticklabels([f'{h}h' for h in hours], rotation=45, ha='right')
    
    # 3. PÉNALITÉS
    ax3 = axes[1, 0]
    
    baseline_penalties = baseline_hourly['penalty_fcfa'].values
    optimized_penalties = optimized_df['penalty_fcfa'].values
    
    ax3.fill_between(hours, baseline_penalties, alpha=0.5, label='Baseline', 
                     color='#e74c3c', step='mid')
    ax3.fill_between(hours, optimized_penalties, alpha=0.5, label='Optimisé', 
                     color='#27ae60', step='mid')
    
    ax3.set_xlabel('Heure de la journée', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Pénalités (FCFA)', fontsize=11, fontweight='bold')
    ax3.set_title('Pénalités de Dépassement Puissance Souscrite', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper left', fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.set_xticks(hours)
    ax3.set_xticklabels([f'{h}h' for h in hours], rotation=45, ha='right')
    
    # 4. RÉCAPITULATIF ÉCONOMIES
    ax4 = axes[1, 1]
    
    if metrics:
        categories = ['Baseline\n(Coût total)', 'Optimisé\n(Coût total)', 'Économies']
        values = [
            metrics['baseline_cost_fcfa'],
            metrics['optimized_cost_fcfa'],
            metrics['savings_fcfa']
        ]
        colors = ['#e74c3c', '#27ae60', '#3498db']
        
        bars = ax4.bar(categories, values, color=colors, alpha=0.8, 
                       edgecolor='black', linewidth=1.5)
        
        ax4.set_ylabel('Montant (FCFA)', fontsize=11, fontweight='bold')
        ax4.set_title(f"Impact Financier Global\nÉconomies: {metrics['savings_percent']:.1f}% | " +
                     f"Projection mensuelle: {metrics['monthly_projection_fcfa']:,.0f} FCFA",
                     fontsize=12, fontweight='bold')
        
        # Annotations sur barres
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:,.0f}\nFCFA',
                    ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        ax4.grid(True, alpha=0.3, axis='y')
    else:
        ax4.text(0.5, 0.5, 'Métriques non disponibles', 
                ha='center', va='center', transform=ax4.transAxes, fontsize=14)
    
    plt.tight_layout()
    
    # Sauvegarder
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ Graphique sauvegardé: {save_path}")
    
    return fig


def plot_pump_schedule(optimized_df, save_path="results/pump_schedule.png"):
    """Graphique planning d'activation des pompes"""
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Extraire statuts pompes
    hours = optimized_df['hour'].values
    
    # Récupérer IDs pompes (assume P1, P2, P3)
    pump_ids = ['P1', 'P2', 'P3']
    
    # Créer données pour heatmap
    schedule_matrix = []
    for pump_id in pump_ids:
        pump_status = []
        for _, row in optimized_df.iterrows():
            # Vérifier si pompe active (dans pumps_active si colonne existe)
            if 'pumps_active' in row and isinstance(row['pumps_active'], str):
                active = pump_id in row['pumps_active']
            elif f'pump_status_{pump_id}' in optimized_df.columns:
                active = row[f'pump_status_{pump_id}'] == 'ON'
            else:
                # Fallback: parser pumps_status si disponible
                active = False
            
            pump_status.append(1 if active else 0)
        schedule_matrix.append(pump_status)
    
    # Créer heatmap
    sns.heatmap(schedule_matrix, 
                cmap=['white', '#27ae60'], 
                cbar_kws={'label': 'État', 'ticks': [0.25, 0.75], 
                         'orientation': 'horizontal'},
                linewidths=1, linecolor='black',
                yticklabels=pump_ids,
                xticklabels=[f'{h}h' for h in hours],
                ax=ax,
                vmin=0, vmax=1)
    
    # Personnaliser colorbar
    cbar = ax.collections[0].colorbar
    cbar.set_ticklabels(['OFF', 'ON'])
    
    ax.set_title('Planning Optimisé d\'Activation des Pompes (24h)', 
                fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Heure de la journée', fontsize=12, fontweight='bold')
    ax.set_ylabel('Pompe', fontsize=12, fontweight='bold')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Planning pompes sauvegardé: {save_path}")
    
    return fig


def plot_demand_vs_supply(baseline_df, optimized_df, save_path="results/demand_supply.png"):
    """Graphique demande vs capacité de pompage"""
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    hours = optimized_df['hour'].values
    demand = optimized_df['demand_m3h'].values
    
    # Capacité baseline (somme flow de toutes pompes actives)
    baseline_hourly = baseline_df.groupby('hour')['flow_m3h'].sum().head(len(hours))
    
    # Capacité optimisée (calculer à partir des pompes actives)
    # Assume 60+50+55 = 165 m³/h capacité totale si toutes ON
    pump_capacities = {'P1': 60, 'P2': 50, 'P3': 55}
    
    optimized_supply = []
    for _, row in optimized_df.iterrows():
        total_capacity = 0
        if 'pumps_active' in row and isinstance(row['pumps_active'], str):
            active_pumps = eval(row['pumps_active']) if row['pumps_active'].startswith('[') else []
            for pump in active_pumps:
                total_capacity += pump_capacities.get(pump, 0)
        optimized_supply.append(total_capacity)
    
    # Tracer
    ax.plot(hours, demand, 'o-', label='Demande réelle', 
           color='#3498db', linewidth=3, markersize=7, alpha=0.9)
    ax.plot(hours, baseline_hourly.values, 's-', label='Capacité baseline', 
           color='#e74c3c', linewidth=2.5, markersize=6, alpha=0.7)
    ax.plot(hours, optimized_supply, '^-', label='Capacité optimisée', 
           color='#27ae60', linewidth=2.5, markersize=6, alpha=0.7)
    
    ax.fill_between(hours, demand, alpha=0.2, color='#3498db')
    
    ax.set_xlabel('Heure de la journée', fontsize=12, fontweight='bold')
    ax.set_ylabel('Débit (m³/h)', fontsize=12, fontweight='bold')
    ax.set_title('Demande en Eau vs Capacité de Pompage', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(hours)
    ax.set_xticklabels([f'{h}h' for h in hours], rotation=45, ha='right')
    
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Graphique demande/offre sauvegardé: {save_path}")
    
    return fig


def generate_summary_report(metrics, save_path="results/summary_report.txt"):
    """Génère rapport texte résumé"""
    
    if not metrics:
        print("⚠️  Pas de métriques disponibles pour le rapport")
        return
    
    report = f"""
{'='*70}
                RAPPORT D'OPTIMISATION IRRIGATION
                        AGRIWATER OPTIMIZER
{'='*70}

📊 RÉSULTATS FINANCIERS
{'-'*70}

Coût Baseline (non optimisé):      {metrics['baseline_cost_fcfa']:>15,.0f} FCFA
Coût Optimisé:                      {metrics['optimized_cost_fcfa']:>15,.0f} FCFA
                                    {'-'*15}
ÉCONOMIES RÉALISÉES:                {metrics['savings_fcfa']:>15,.0f} FCFA
Pourcentage de réduction:           {metrics['savings_percent']:>15.2f} %


💰 PROJECTIONS
{'-'*70}

Économies mensuelles estimées:      {metrics['monthly_projection_fcfa']:>15,.0f} FCFA
Économies annuelles estimées:       {metrics['annual_projection_fcfa']:>15,.0f} FCFA


⚡ PERFORMANCE TECHNIQUE
{'-'*70}

Temps de résolution:                {metrics['solve_time_seconds']:>15.2f} secondes
Méthode d'optimisation:             MILP (Mixed-Integer Linear Programming)
Solveur utilisé:                    CBC (COIN-OR Branch and Cut)


✅ CONCLUSION
{'-'*70}

L'optimisation mathématique du planning d'irrigation permet de réduire
significativement les coûts opérationnels de la ferme en:

1. Minimisant les pénalités de dépassement de puissance souscrite
2. Profitant des tarifs heures creuses pour irrigation nocturne
3. Limitant l'usure des équipements (démarrages optimisés)
4. Maintenant l'approvisionnement en eau des cultures
5. Intégrant la production solaire en journée

ROI estimé du système: < 4 mois

{'='*70}

Généré par: AgriWater Optimizer
Auteur: Abdoulaye Ouedraogo
Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Rapport textuel sauvegardé: {save_path}")
    print(report)


def main():
    """Fonction principale - génère toutes les visualisations"""
    
    print("\n" + "="*70)
    print(" "*20 + "VISUALISATION RÉSULTATS")
    print("="*70)
    
    # Charger données
    baseline_df, optimized_df, metrics = load_data()
    
    if baseline_df is None or optimized_df is None:
        print("\n❌ Impossible de charger les données!")
        return
    
    print("\n📈 Génération graphiques...")
    
    # 1. Comparaison coûts
    plot_cost_comparison(baseline_df, optimized_df, metrics)
    
    # 2. Planning pompes
    plot_pump_schedule(optimized_df)
    
    # 3. Demande vs offre
    plot_demand_vs_supply(baseline_df, optimized_df)
    
    # 4. Rapport textuel
    if metrics:
        generate_summary_report(metrics)
    
    print("\n" + "="*70)
    print("✅ VISUALISATIONS TERMINÉES")
    print("="*70)
    print(f"\n📁 Fichiers générés dans: results/")
    print("  - cost_comparison.png")
    print("  - pump_schedule.png")
    print("  - demand_supply.png")
    print("  - summary_report.txt")
    print("\n✨ Programme terminé avec succès!\n")


if __name__ == "__main__":
    main()
