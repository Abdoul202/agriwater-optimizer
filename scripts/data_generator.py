"""
AgriWater Optimizer - Data Generator
Générateur de données synthétiques pour système irrigation agricole
Simule consommation énergétique pompes irrigation avec patterns saisonniers
Auteur: Abdoulaye Ouedraogo
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import os

class AgriIrrigationDataGenerator:
    def __init__(self, start_date, days=30, num_pumps=3):
        self.start_date = pd.to_datetime(start_date)
        self.days = days
        self.num_pumps = num_pumps
        self.hours_per_day = 24
        
        # Paramètres réalistes ferme agricole Sahel
        self.tariff_peak = 110      # FCFA/kWh heures pleines (réseau SONABEL)
        self.tariff_offpeak = 75    # FCFA/kWh heures creuses
        self.subscribed_power = 150  # kW (puissance souscrite)
        self.penalty_rate = 200      # FCFA/kW dépassé
        self.solar_contribution = 0.3  # 30% couvert par solaire en journée
        
        # Configurations pompes irrigation
        self.pump_configs = [
            {"id": "P1", "capacity_m3h": 60, "power_kw": 45, "efficiency": 0.75, "age_years": 5, "type": "principale"},
            {"id": "P2", "capacity_m3h": 50, "power_kw": 38, "efficiency": 0.72, "age_years": 8, "type": "secondaire"},
            {"id": "P3", "capacity_m3h": 55, "power_kw": 42, "efficiency": 0.73, "age_years": 3, "type": "appoint"},
        ]
        
    def generate_demand_pattern(self):
        """Génère pattern de demande irrigation réaliste pour ferme maraîchère"""
        hours = self.days * self.hours_per_day
        timestamps = [self.start_date + timedelta(hours=h) for h in range(hours)]
        
        demand = []
        for ts in timestamps:
            hour = ts.hour
            day_of_week = ts.weekday()
            day_of_month = ts.day
            
            # Pattern irrigation journalier (m³/h)
            # Irrigation principalement tôt le matin et en soirée (évaporation minimale)
            base_demand = 50
            
            # Pics irrigation optimaux
            if 5 <= hour <= 8:  # Matin (optimal pour irrigation)
                base_demand = 120
            elif 18 <= hour <= 21:  # Soir (2ème session)
                base_demand = 100
            elif 11 <= hour <= 15:  # Midi - minimiser (évaporation élevée)
                base_demand = 30
            elif 22 <= hour or hour <= 4:  # Nuit (minimal - sécurité)
                base_demand = 20
                
            # Pas de weekend en agriculture
            # Légère réduction dimanche (maintenance)
            if day_of_week == 6:
                base_demand *= 0.70
                
            # Variation saisonnière (cultures)
            month = ts.month
            if month in [11, 12, 1, 2, 3, 4]:  # Saison sèche - irrigation intensive
                base_demand *= 1.35
            elif month in [6, 7, 8, 9]:  # Saison pluies - irrigation réduite
                base_demand *= 0.60
            elif month in [5, 10]:  # Transitions
                base_demand *= 0.85
                
            # Cycles culturaux (peaks tous les 7-10 jours)
            if day_of_month % 7 in [1, 2]:  # Pics besoins après semis/repiquage
                base_demand *= 1.20
                
            # Ajouter variabilité réaliste (météo, évaporation)
            noise = np.random.normal(0, base_demand * 0.12)
            final_demand = max(15, base_demand + noise)
            
            demand.append(final_demand)
            
        return timestamps, demand
    
    def calculate_pump_energy(self, flow, pump_config, hour_running):
        """Calcule consommation énergétique réelle d'une pompe"""
        
        # Puissance théorique proportionnelle au débit
        theoretical_power = (flow / pump_config["capacity_m3h"]) * pump_config["power_kw"]
        
        # Facteurs d'inefficience
        efficiency = pump_config["efficiency"]
        age_factor = 1 + (pump_config["age_years"] * 0.02)  # 2% perte/an
        
        # Variabilité opérationnelle
        operational_variance = np.random.uniform(0.95, 1.05)
        
        # Puissance réelle
        actual_power = (theoretical_power / efficiency) * age_factor * operational_variance
        
        return actual_power
    
    def generate_pump_data(self, timestamps, demand):
        """Génère données de pompage basées sur demande - BASELINE (non optimisé)"""
        
        data = []
        
        for i, (ts, dem) in enumerate(zip(timestamps, demand)):
            hour = ts.hour
            
            # Stratégie BASELINE naive: activer pompes par ordre jusqu'à satisfaire demande
            active_pumps = []
            remaining_demand = dem
            total_power = 0
            total_flow = 0
            
            # Activation séquentielle des pompes
            for pump in self.pump_configs:
                if remaining_demand > 0:
                    # Débit fourni par cette pompe
                    flow = min(pump["capacity_m3h"], remaining_demand)
                    
                    # Calcul consommation énergétique
                    power_used = self.calculate_pump_energy(flow, pump, i % 24)
                    
                    # Possibilité de fuite (10% des enregistrements)
                    leak_detected = False
                    leak_factor = 1.0
                    if np.random.random() < 0.10:
                        leak_detected = True
                        leak_factor = np.random.uniform(1.08, 1.20)
                        power_used *= leak_factor  # Surconsommation due à fuite
                    
                    active_pumps.append({
                        "pump_id": pump["id"],
                        "flow_m3h": flow,
                        "power_kw": power_used,
                        "status": "ON",
                        "leak_detected": leak_detected
                    })
                    
                    total_power += power_used
                    total_flow += flow
                    remaining_demand -= flow
                else:
                    active_pumps.append({
                        "pump_id": pump["id"],
                        "flow_m3h": 0,
                        "power_kw": 0,
                        "status": "OFF",
                        "leak_detected": False
                    })
            
            # Calcul tarifaire
            tariff = self.tariff_offpeak if (hour < 7 or hour >= 23) else self.tariff_peak
            
            # Calcul pénalités si dépassement puissance souscrite
            penalty = 0
            if total_power > self.subscribed_power:
                exceeded_power = total_power - self.subscribed_power
                penalty = exceeded_power * self.penalty_rate
            
            # Coûts
            energy_cost = total_power * tariff
            total_cost = energy_cost + penalty
            
            # Enregistrement pour chaque pompe
            for pump_data in active_pumps:
                num_active = len([p for p in active_pumps if p["status"] == "ON"])
                
                data.append({
                    "timestamp": ts,
                    "hour": hour,
                    "day_of_week": ts.weekday(),
                    "pump_id": pump_data["pump_id"],
                    "demand_m3h": dem,
                    "flow_m3h": pump_data["flow_m3h"],
                    "power_kw": pump_data["power_kw"],
                    "status": pump_data["status"],
                    "tariff_fcfa_kwh": tariff,
                    "tariff_type": "offpeak" if (hour < 7 or hour >= 23) else "peak",
                    "energy_cost_fcfa": pump_data["power_kw"] * tariff,
                    "penalty_fcfa": penalty / num_active if (num_active > 0 and penalty > 0) else 0,
                    "total_cost_fcfa": (pump_data["power_kw"] * tariff + (penalty / num_active if num_active > 0 else 0)),
                    "total_power_kw": total_power,
                    "subscribed_power_kw": self.subscribed_power,
                    "power_exceeded": total_power > self.subscribed_power,
                    "leak_detected": pump_data["leak_detected"]
                })
        
        return pd.DataFrame(data)
    
    def generate_dataset(self, output_file="data/pumping_data.csv"):
        """Génère dataset complet et sauvegarde"""
        
        print("="*60)
        print("AGRIWATER - GÉNÉRATEUR DONNÉES IRRIGATION")
        print("="*60)
        print(f"\n📊 Configuration:")
        print(f"  - Période: {self.days} jours")
        print(f"  - Date début: {self.start_date.strftime('%Y-%m-%d')}")
        print(f"  - Nombre pompes: {self.num_pumps}")
        print(f"  - Puissance souscrite: {self.subscribed_power} kW")
        print(f"  - Tarif HP: {self.tariff_peak} FCFA/kWh")
        print(f"  - Tarif HC: {self.tariff_offpeak} FCFA/kWh")
        print(f"  - Contribution solaire: {self.solar_contribution*100:.0f}%")
        print(f"\n⚙️  Génération en cours...")
        
        # Générer patterns
        timestamps, demand = self.generate_demand_pattern()
        print(f"  ✓ Patterns demande générés: {len(demand)} points")
        
        # Générer données pompage
        df = self.generate_pump_data(timestamps, demand)
        print(f"  ✓ Données pompage générées: {len(df)} enregistrements")
        
        # Créer dossier si nécessaire
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        
        # Sauvegarder
        df.to_csv(output_file, index=False)
        print(f"  ✓ Fichier sauvegardé: {output_file}")
        
        # Statistiques
        print(f"\n📈 Statistiques BASELINE (non optimisé):")
        print(f"  - Période: {df['timestamp'].min()} → {df['timestamp'].max()}")
        print(f"  - Coût total: {df['total_cost_fcfa'].sum():,.0f} FCFA")
        print(f"  - Coût énergie: {df['energy_cost_fcfa'].sum():,.0f} FCFA")
        print(f"  - Pénalités: {df['penalty_fcfa'].sum():,.0f} FCFA ({df['penalty_fcfa'].sum()/df['total_cost_fcfa'].sum()*100:.1f}%)")
        print(f"  - Énergie totale: {df['power_kw'].sum():,.0f} kWh")
        print(f"  - Dépassements: {df['power_exceeded'].sum()} occurrences")
        print(f"  - Fuites détectées: {df['leak_detected'].sum()} cas")
        
        # Stats par pompe
        print(f"\n🔧 Par pompe:")
        for pump_id in df['pump_id'].unique():
            pump_data = df[df['pump_id'] == pump_id]
            active_hours = (pump_data['status'] == 'ON').sum()
            total_energy = pump_data['power_kw'].sum()
            total_cost = pump_data['total_cost_fcfa'].sum()
            print(f"  {pump_id}: {active_hours}h actif | {total_energy:,.0f} kWh | {total_cost:,.0f} FCFA")
        
        # Débit moyen par période
        hourly_avg = df.groupby('hour')['demand_m3h'].mean()
        peak_hour = hourly_avg.idxmax()
        print(f"\n⏰ Heure pic demande: {peak_hour}h ({hourly_avg[peak_hour]:.1f} m³/h)")
        
        print("="*60)
        print("✅ GÉNÉRATION TERMINÉE\n")
        
        return df
    
    def save_config(self, output_file="data/generator_config.json"):
        """Sauvegarde configuration pour reproductibilité"""
        
        config = {
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "days": self.days,
            "num_pumps": self.num_pumps,
            "tariff_peak": self.tariff_peak,
            "tariff_offpeak": self.tariff_offpeak,
            "subscribed_power": self.subscribed_power,
            "penalty_rate": self.penalty_rate,
            "pump_configs": self.pump_configs
        }
        
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Configuration sauvegardée: {output_file}")


if __name__ == "__main__":
    print("\n🚀 AgriWater Optimizer - Générateur de données\n")
    
    # Configuration
    generator = AgriIrrigationDataGenerator(
        start_date="2026-01-01",
        days=30,
        num_pumps=3
    )
    
    # Génération
    df = generator.generate_dataset(output_file="data/irrigation_data.csv")
    generator.save_config(output_file="data/generator_config.json")
    
    print("✨ Programme terminé avec succès!")
