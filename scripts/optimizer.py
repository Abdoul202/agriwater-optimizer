"""
AgriWater Optimizer - Scheduling Engine
Optimiseur de planning irrigation sous contraintes énergétiques multiples
Minimise coûts (réseau + solaire) via programmation linéaire mixte (MILP)
Auteur: Abdoulaye Ouedraogo
"""

import pandas as pd
import numpy as np
from pulp import *
from datetime import datetime, timedelta
import json
import os

class IrrigationScheduleOptimizer:
    def __init__(self, demand_forecast, pump_configs, tariff_config):
        """
        Initialise optimiseur
        
        Args:
            demand_forecast: Liste demandes horaires (m³/h)
            pump_configs: Liste configs pompes [{id, capacity_m3h, power_kw}, ...]
            tariff_config: Dict tarifs {peak, offpeak, subscribed_power, penalty_rate}
        """
        self.demand = demand_forecast
        self.pumps = pump_configs
        self.tariff = tariff_config
        self.solution = None
        
    def build_optimization_problem(self, horizon_hours=24):
        """Construit problème d'optimisation MILP"""
        
        print(f"\n🔧 Construction problème optimisation...")
        print(f"  - Horizon: {horizon_hours} heures")
        print(f"  - Pompes: {len(self.pumps)}")
        print(f"  - Variables de décision: {len(self.pumps) * horizon_hours}")
        
        # Créer problème
        prob = LpProblem("AgriWater_Irrigation_Scheduling", LpMinimize)
        
        # VARIABLES DE DÉCISION
        
        # pump_status[p, t] ∈ {0, 1} : pompe p active à l'heure t
        pump_status = {}
        for p in self.pumps:
            for t in range(horizon_hours):
                pump_status[(p['id'], t)] = LpVariable(
                    f"pump_{p['id']}_h{t}", 
                    cat='Binary'
                )
        
        # total_power[t] : puissance totale appelée à l'heure t
        total_power = {}
        for t in range(horizon_hours):
            total_power[t] = LpVariable(f"total_power_h{t}", lowBound=0)
        
        # penalty[t] : pénalité de dépassement à l'heure t
        penalty = {}
        for t in range(horizon_hours):
            penalty[t] = LpVariable(f"penalty_h{t}", lowBound=0)
        
        # startup[p, t] : indicateur démarrage pompe p à l'heure t
        startup = {}
        for p in self.pumps:
            for t in range(horizon_hours):
                startup[(p['id'], t)] = LpVariable(
                    f"startup_{p['id']}_h{t}",
                    cat='Binary'
                )
        
        # FONCTION OBJECTIF: Minimiser coût total
        
        objective = lpSum([
            # Coût énergie horaire
            total_power[t] * (
                self.tariff['peak'] if (7 <= t < 23) else self.tariff['offpeak']
            )
            # Pénalités dépassement
            + penalty[t]
            # Coût démarrages (usure équipements)
            + lpSum([startup[(p['id'], t)] * 5000 for p in self.pumps])
            
            for t in range(horizon_hours)
        ])
        
        prob += objective
        
        print(f"  ✓ Fonction objectif définie")
        
        # CONTRAINTES
        
        constraint_count = 0
        
        # 1. SATISFAIRE LA DEMANDE
        for t in range(horizon_hours):
            prob += (
                lpSum([
                    pump_status[(p['id'], t)] * p['capacity_m3h'] 
                    for p in self.pumps
                ]) >= self.demand[t],
                f"demand_satisfaction_h{t}"
            )
            constraint_count += 1
        
        # 2. CALCUL PUISSANCE TOTALE
        for t in range(horizon_hours):
            prob += (
                total_power[t] == lpSum([
                    pump_status[(p['id'], t)] * p['power_kw'] 
                    for p in self.pumps
                ]),
                f"total_power_calc_h{t}"
            )
            constraint_count += 1
        
        # 3. CALCUL PÉNALITÉS (si dépassement puissance souscrite)
        for t in range(horizon_hours):
            prob += (
                penalty[t] >= self.tariff['penalty_rate'] * (
                    total_power[t] - self.tariff['subscribed_power']
                ),
                f"penalty_calc_h{t}"
            )
            constraint_count += 1
        
        # 4. DÉTECTION DÉMARRAGES
        for p in self.pumps:
            for t in range(1, horizon_hours):
                # startup = 1 si pompe passe de OFF à ON
                prob += (
                    startup[(p['id'], t)] >= pump_status[(p['id'], t)] - pump_status[(p['id'], t-1)],
                    f"startup_detect_{p['id']}_h{t}"
                )
                constraint_count += 1
        
        # 5. DURÉE MINIMALE DE FONCTIONNEMENT (relâchée - optionnel)
        # DÉSACTIVÉ pour éviter infaisabilité
        # min_runtime_hours = 2
        # for p in self.pumps:
        #     for t in range(horizon_hours - min_runtime_hours):
        #         for delta in range(1, min_runtime_hours):
        #             if t + delta < horizon_hours:
        #                 prob += (
        #                     pump_status[(p['id'], t + delta)] >= 
        #                     pump_status[(p['id'], t)] - pump_status[(p['id'], t-1)] if t > 0 else pump_status[(p['id'], t)],
        #                     f"min_runtime_{p['id']}_h{t}_delta{delta}"
        #                 )
        #                 constraint_count += 1
        
        # 6. REDONDANCE: autoriser toutes pompes actives si nécessaire (relâchée)
        # DÉSACTIVÉ - peut causer infaisabilité avec forte demande
        # for t in range(horizon_hours):
        #     prob += (
        #         lpSum([pump_status[(p['id'], t)] for p in self.pumps]) <= len(self.pumps) - 1,
        #         f"redundancy_h{t}"
        #     )
        #     constraint_count += 1
        
        # 7. LIMITE DÉMARRAGES PAR POMPE (relâchée à 8/jour)
        for p in self.pumps:
            prob += (
                lpSum([startup[(p['id'], t)] for t in range(min(24, horizon_hours))]) <= 8,
                f"max_startups_{p['id']}"
            )
            constraint_count += 1
        
        print(f"  ✓ {constraint_count} contraintes ajoutées")
        
        return prob, pump_status, total_power, penalty, startup
    
    def optimize_schedule(self, horizon_hours=24):
        """Exécute optimisation"""
        
        print("\n" + "="*60)
        print("AGRIWATER - OPTIMISATION PLANNING IRRIGATION")
        print("="*60)
        
        # Vérifications préliminaires
        if len(self.demand) < horizon_hours:
            print(f"⚠️  Avertissement: Demande sur {len(self.demand)}h seulement")
            horizon_hours = len(self.demand)
        
        # Construire problème
        prob, pump_status, total_power, penalty, startup = self.build_optimization_problem(horizon_hours)
        
        # Résoudre
        print(f"\n🚀 Lancement solveur MILP...")
        start_time = datetime.now()
        
        solver = PULP_CBC_CMD(msg=1, timeLimit=60)  # Max 60s
        prob.solve(solver)
        
        solve_time = (datetime.now() - start_time).total_seconds()
        
        # Résultats
        status = LpStatus[prob.status]
        print(f"\n📊 Résolution terminée en {solve_time:.2f}s")
        print(f"  - Statut: {status}")
        
        if status != "Optimal":
            print(f"⚠️  ATTENTION: Solution non optimale!")
            if status == "Infeasible":
                print("  → Problème infaisable (contraintes impossibles à satisfaire)")
            elif status == "Unbounded":
                print("  → Problème non borné")
            return None
        
        # Extraction solution
        schedule = []
        total_cost_optimized = 0
        total_energy = 0
        total_penalties = 0
        
        for t in range(horizon_hours):
            hour_data = {
                'hour': t,
                'demand_m3h': self.demand[t],
                'total_power_kw': total_power[t].varValue,
                'penalty_fcfa': penalty[t].varValue if penalty[t].varValue else 0,
                'tariff_fcfa_kwh': self.tariff['peak'] if (7 <= t < 23) else self.tariff['offpeak'],
                'pumps_active': [],
                'pumps_status': {}
            }
            
            # État pompes
            for p in self.pumps:
                status_val = pump_status[(p['id'], t)].varValue
                hour_data['pumps_status'][p['id']] = 'ON' if status_val > 0.5 else 'OFF'
                if status_val > 0.5:
                    hour_data['pumps_active'].append(p['id'])
            
            # Calcul coût heure
            energy_cost = hour_data['total_power_kw'] * hour_data['tariff_fcfa_kwh']
            hour_data['energy_cost_fcfa'] = energy_cost
            hour_data['total_cost_fcfa'] = energy_cost + hour_data['penalty_fcfa']
            
            total_cost_optimized += hour_data['total_cost_fcfa']
            total_energy += hour_data['total_power_kw']
            total_penalties += hour_data['penalty_fcfa']
            
            schedule.append(hour_data)
        
        self.solution = {
            'schedule': pd.DataFrame(schedule),
            'total_cost': total_cost_optimized,
            'total_energy': total_energy,
            'total_penalties': total_penalties,
            'status': status,
            'solve_time': solve_time
        }
        
        print(f"\n💰 Coût optimisé: {total_cost_optimized:,.0f} FCFA")
        print(f"  - Énergie: {total_energy:,.1f} kWh")
        print(f"  - Pénalités: {total_penalties:,.0f} FCFA ({total_penalties/total_cost_optimized*100:.1f}%)")
        
        return self.solution
    
    def compare_baseline_vs_optimized(self, baseline_data):
        """Compare solution baseline vs optimisée"""
        
        print("\n" + "="*60)
        print("COMPARAISON BASELINE vs OPTIMISÉ")
        print("="*60)
        
        if self.solution is None:
            print("❌ Pas de solution optimisée disponible!")
            return None
        
        # Calcul baseline sur même horizon
        horizon = len(self.solution['schedule'])
        baseline_subset = baseline_data.head(horizon * len(self.pumps))
        
        baseline_cost = baseline_subset['total_cost_fcfa'].sum()
        baseline_energy = baseline_subset['power_kw'].sum()
        baseline_penalties = baseline_subset['penalty_fcfa'].sum()
        
        optimized_cost = self.solution['total_cost']
        optimized_energy = self.solution['total_energy']
        optimized_penalties = self.solution['total_penalties']
        
        # Gains
        cost_savings = baseline_cost - optimized_cost
        cost_savings_pct = (cost_savings / baseline_cost) * 100
        
        energy_savings = baseline_energy - optimized_energy
        energy_savings_pct = (energy_savings / baseline_energy) * 100
        
        penalty_savings = baseline_penalties - optimized_penalties
        penalty_savings_pct = (penalty_savings / baseline_penalties) * 100 if baseline_penalties > 0 else 0
        
        print(f"\n📊 Résultats sur {horizon}h:")
        print(f"\n  COÛTS:")
        print(f"    Baseline:   {baseline_cost:>12,.0f} FCFA")
        print(f"    Optimisé:   {optimized_cost:>12,.0f} FCFA")
        print(f"    Économies:  {cost_savings:>12,.0f} FCFA ({cost_savings_pct:>5.1f}%)")
        
        print(f"\n  ÉNERGIE:")
        print(f"    Baseline:   {baseline_energy:>12,.1f} kWh")
        print(f"    Optimisé:   {optimized_energy:>12,.1f} kWh")
        print(f"    Économies:  {energy_savings:>12,.1f} kWh ({energy_savings_pct:>5.1f}%)")
        
        print(f"\n  PÉNALITÉS:")
        print(f"    Baseline:   {baseline_penalties:>12,.0f} FCFA")
        print(f"    Optimisé:   {optimized_penalties:>12,.0f} FCFA")
        print(f"    Réduction:  {penalty_savings:>12,.0f} FCFA ({penalty_savings_pct:>5.1f}%)")
        
        # Projection mensuelle
        hours_per_month = 720
        monthly_savings = (cost_savings / horizon) * hours_per_month
        annual_savings = monthly_savings * 12
        
        print(f"\n💵 PROJECTION:")
        print(f"    Économies mensuelles:  ~{monthly_savings:,.0f} FCFA")
        print(f"    Économies annuelles:   ~{annual_savings:,.0f} FCFA")
        
        print("="*60)
        
        return {
            'baseline_cost': baseline_cost,
            'optimized_cost': optimized_cost,
            'savings_fcfa': cost_savings,
            'savings_percent': cost_savings_pct,
            'energy_savings_kwh': energy_savings,
            'penalty_reduction': penalty_savings,
            'monthly_savings_projection': monthly_savings,
            'annual_savings_projection': annual_savings,
            'schedule': self.solution['schedule']
        }


def run_optimization_demo():
    """Fonction démo complète"""
    
    print("\n" + "="*70)
    print(" "*15 + "AGRIWATER OPTIMIZER - DEMO")
    print("="*70)
    
    # Charger données baseline
    print("\n📂 Chargement données baseline...")
    try:
        baseline_df = pd.read_csv("data/irrigation_data.csv")
        baseline_df['timestamp'] = pd.to_datetime(baseline_df['timestamp'])
        print(f"  ✓ {len(baseline_df)} enregistrements chargés")
    except FileNotFoundError:
        print("  ❌ Fichier data/irrigation_data.csv introuvable!")
        print("  → Exécutez d'abord: python data_generator.py")
        return
    
    # Extraire demande pour optimisation (24h)
    horizon = 24
    demand_hourly = baseline_df.groupby('hour')['demand_m3h'].mean().tolist()[:horizon]
    
    # Configuration pompes
    pump_configs = [
        {"id": "P1", "capacity_m3h": 60, "power_kw": 45},
        {"id": "P2", "capacity_m3h": 50, "power_kw": 38},
        {"id": "P3", "capacity_m3h": 55, "power_kw": 42},
    ]
    
    # Configuration tarifs
    tariff_config = {
        'peak': 110,
        'offpeak': 75,
        'subscribed_power': 150,
        'penalty_rate': 200
    }
    
    # Créer optimiseur
    optimizer = IrrigationScheduleOptimizer(demand_hourly, pump_configs, tariff_config)
    
    # Optimiser
    result = optimizer.optimize_schedule(horizon_hours=horizon)
    
    if result:
        # Comparer avec baseline
        comparison = optimizer.compare_baseline_vs_optimized(baseline_df)
        
        # Sauvegarder résultats
        os.makedirs("results", exist_ok=True)
        
        result['schedule'].to_csv("results/optimized_schedule.csv", index=False)
        print(f"\n💾 Planning optimisé sauvegardé: results/optimized_schedule.csv")
        
        # Sauvegarder métriques
        with open("results/optimization_metrics.json", 'w') as f:
            metrics = {
                'baseline_cost_fcfa': float(comparison['baseline_cost']),
                'optimized_cost_fcfa': float(comparison['optimized_cost']),
                'savings_fcfa': float(comparison['savings_fcfa']),
                'savings_percent': float(comparison['savings_percent']),
                'monthly_projection_fcfa': float(comparison['monthly_savings_projection']),
                'annual_projection_fcfa': float(comparison['annual_savings_projection']),
                'solve_time_seconds': result['solve_time']
            }
            json.dump(metrics, f, indent=2)
        
        print(f"💾 Métriques sauvegardées: results/optimization_metrics.json")
        
        print("\n✅ OPTIMISATION TERMINÉE AVEC SUCCÈS!\n")
        
        return comparison
    else:
        print("\n❌ Échec optimisation\n")
        return None


if __name__ == "__main__":
    run_optimization_demo()
