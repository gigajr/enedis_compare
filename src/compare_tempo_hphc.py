#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ======================================================================================================================
# Difference de prix entre un abonnement HP/HC et Tempo sur une période donnée (fichier données csv à extraire sur
# l'espace personnel ENEDIS)
# ======================================================================================================================
# Author: Julien Ros
# Company: Ros Company
# Date: 9 November 2022
# ======================================================================================================================
import argparse
import sys
import pandas as pd
import plotly.express as px
from datetime import datetime

# Abonnement HP/HC 12 kVA
ABONNEMENT_ANNUEL_TEMPO = 218.52
TARIF_BLEU_HP = 0.1272
TARIF_BLEU_HC = 0.0862
TARIF_ROUGE_HP = 0.5486
TARIF_ROUGE_HC = 0.1222
TARIF_BLANC_HP = 0.1653
TARIF_BLANC_HC = 0.1112

# Abonnement Tempo 12 kVA
ABONNEMENT_ANNUEL_HP_HC = 221.81
TARIF_HP = 0.1841
TARIF_HC = 0.1470

# ======================================================================================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Outil de comparaison des tarifs HP/HC et Tempo')
    parser.add_argument('-f', '--filename', help='Fichier csv Enedis', type=str, required=True)

    args = parser.parse_args()

    with open(args.filename, 'r') as fp:
        nbLines = sum(1 for line in fp)

    consoDataFrame = pd.read_csv(args.filename, delimiter=';', skiprows=[0, 1, nbLines - 3, nbLines - 2, nbLines - 1],
                                 parse_dates=['Horodate'])
    consoDataFrame['Heure Pleine'] = consoDataFrame['EAS F1'].diff()  # Consommation HP en Wh
    consoDataFrame['Heure Creuse'] = consoDataFrame['EAS F2'].diff()  # Consommation HC en Wh

    # Courbe avec les 2 consommations dans le temps
    fig = px.bar(consoDataFrame, x='Horodate', y=['Heure Pleine', 'Heure Creuse'], barmode='group',
                 title='Consommation en Wh')
    fig.show()
    fig.write_html('consommation.html')

    # Camembert de répartition des consommations
    consoTotaleDataFrame = pd.DataFrame(
        {
            'Consommation par période en kWh': [
                consoDataFrame['Heure Pleine'].sum() / 1000,
                consoDataFrame['Heure Creuse'].sum() / 1000,
            ],
            'Périodes': ['Heure Pleine', 'Heure Creuse'],
        }
    )
    fig = px.pie(consoTotaleDataFrame, values='Consommation par période en kWh', names='Périodes',
                 title='Répartition de la consommation sur la période')
    fig.show()
    fig.write_html('hp_hc.html')


    # Prix au tarif Abonnement HP/HC
    consoDataFrame['Horodate'] = pd.to_datetime(consoDataFrame['Horodate'], utc=True, format='%Y-%m-%d')
    coutTotal = consoDataFrame[['Horodate']].copy()
    coutTotal['Cout Heure Creuse'] = (consoDataFrame['Heure Creuse'] / 1000) * TARIF_HC
    coutTotal['Cout Heure Pleine'] = (consoDataFrame['Heure Pleine'] / 1000) * TARIF_HP
    coutTotal['Cout Total HP/HC'] = coutTotal['Cout Heure Creuse'] + coutTotal['Cout Heure Creuse']
    coutPeriode = coutTotal['Cout Total HP/HC'].sum() + len(
        coutTotal['Horodate'].dt.month.unique()) * ABONNEMENT_ANNUEL_HP_HC / 12
    print('Prix au tarif HP/HC: %f' % (coutPeriode))

    # Prix au tarif Tempo
    # 43 J par an
    jourBlanc = ['2022-01-05', '2022-01-07', '2022-01-15', '2022-01-22', '2022-01-28', '2022-01-31', '2022-02-02',
                 '2022-02-03', '2022-02-07', '2022-02-08', '2022-02-09', '2022-02-10', '2022-02-11', '2022-02-23',
                 '2022-02-25', '2022-02-28', '2022-03-01', '2022-03-02', '2022-03-03', '2022-03-07', '2022-03-08',
                 '2022-04-04', '2022-04-05', '2022-04-06', '2022-04-14', '2022-05-24', '2022-05-30', '2022-05-31']
    jourBlanc = [datetime.strptime(date, '%Y-%m-%d').date() for date in jourBlanc]
    consoDataFrame['jourBlanc'] = consoDataFrame['Horodate'].apply(lambda date: date.date() in jourBlanc)
    coutTotal['Cout Blanc Heure Creuse'] = consoDataFrame['jourBlanc'] * (
                consoDataFrame['Heure Creuse'] / 1000) * TARIF_BLANC_HC
    coutTotal['Cout Blanc Heure Pleine'] = consoDataFrame['jourBlanc'] * (
                consoDataFrame['Heure Pleine'] / 1000) * TARIF_BLANC_HP

    # 22 J par an
    jourRouge = ['2022-01-06', '2022-01-10', '2022-01-11', '2022-01-12', '2022-01-13', '2022-01-14', '2022-01-17',
                 '2022-01-18', '2022-01-19', '2022-01-20', '2022-01-21', '2022-01-19', '2022-01-24', '2022-01-25',
                 '2022-01-26', '2022-01-27']
    jourRouge = [datetime.strptime(date, '%Y-%m-%d').date() for date in jourRouge]
    consoDataFrame['jourRouge'] = consoDataFrame['Horodate'].apply(lambda date: date.date() in jourRouge)
    coutTotal['Cout Rouge Heure Creuse'] = consoDataFrame['jourRouge'] * (
                consoDataFrame['Heure Creuse'] / 1000) * TARIF_ROUGE_HC
    coutTotal['Cout Rouge Heure Pleine'] = consoDataFrame['jourRouge'] * (
                consoDataFrame['Heure Pleine'] / 1000) * TARIF_ROUGE_HP

    # 300 J par an
    consoDataFrame['jourBleu'] = ~(consoDataFrame['jourRouge'] | consoDataFrame['jourBlanc'])
    coutTotal['Cout Bleu Heure Creuse'] = consoDataFrame['jourBleu'] * (
                consoDataFrame['Heure Creuse'] / 1000) * TARIF_BLEU_HC
    coutTotal['Cout Bleu Heure Pleine'] = consoDataFrame['jourBleu'] * (
                consoDataFrame['Heure Pleine'] / 1000) * TARIF_BLEU_HP

    coutTotal['Cout Total Tempo'] = coutTotal['Cout Bleu Heure Creuse'] + coutTotal['Cout Bleu Heure Pleine'] + \
                                    coutTotal[
                                        'Cout Blanc Heure Creuse'] + coutTotal['Cout Blanc Heure Pleine'] + coutTotal[
                                        'Cout Rouge Heure Creuse'] + \
                                    coutTotal['Cout Rouge Heure Pleine']

    coutPeriode = coutTotal['Cout Total Tempo'].sum() + len(
        coutTotal['Horodate'].dt.month.unique()) * ABONNEMENT_ANNUEL_TEMPO / 12
    print('Prix au tarif Tempo: %f' % (coutPeriode))

    # Courbe avec les 2 couts dans le temps
    print(coutTotal.head(10))
    fig = px.bar(coutTotal, x='Horodate', y=['Cout Total Tempo', 'Cout Total HP/HC'], barmode='group',
                 title='Consommation en €')
    fig.show()
    fig.write_html('cout.html')

    sys.exit(0)
