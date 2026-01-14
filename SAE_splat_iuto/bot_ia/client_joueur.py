# coding: utf-8
"""
Projet Splat'IUT'O

Licence pédagogique — usage académique uniquement                                                    
Copyright (c) 2026 Limet Sébastien / IUT'O, Université d'Orléans

Ce code est fourni exclusivement dans un cadre pédagogique.
Les étudiants sont autorisés à l’utiliser et le modifier uniquement
pour les besoins du projet évalué dans le cadre de la SAE1.02 du BUT Informatique d'Orléans.

Toute diffusion, publication ou réutilisation en dehors de ce cadre,
notamment sur des plateformes publiques, est interdite sans
autorisation écrite préalable de l’auteur.

Tous droits réservés.

Module contenant l'implémentation de l'IA et le programme principal du joueur
"""

#Notes : Le bidon quand on est en positif remonte à 20 la réserve

import argparse
import random

import copy

from bot_ia  import client
from bot_ia  import const
from bot_ia  import plateau
from bot_ia  import case
from bot_ia  import joueur


def analyse_case(plateau,joueur): # plateau est un dico représenté comme ça: {"nb_lignes" : ..., "nb_colonnes" : ..., "les_valeurs": une liste de dictionnaires}
    resultat = {"persos": [], "adversaire" :[], "vides" :[]}
    liste_cases = plateau["les_valeurs"]
    lignes = plateau["nb_lignes"]
    colonnes = plateau["nb_colonnes"]
    for i in range(lignes) :
         la_ligne = liste_cases[i]
         for j in range(colonnes) :
              case_actuelle = la_ligne[j]
              couleur = case.get_couleur(case_actuelle) == joueur["couleur"] 
              if couleur == joueur["couleur"] :
                  resultat["persos"].append((i,j))
              elif couleur == ' ' or case.get_couleur(case_actuelle) == None : 
                  resultat["vides"].append((i,j))
              else :
                 resultat["adversaire"].append((i,j)) 
    return resultat  

def trouver_mon_joueur(ma_couleur,les_joueurs):
    """Trouve mon joueur (=joueur qui a ma couleur)

    Args:
        ma_couleur (str): ma couleur = la couleur de mon joueur
        les_joueurs (list): une liste de joueurs avec leurs caractéristiques (liste de dictionnaires)

    Returns:
        dict: mon joueur et ses caractéristiques
    """    
    return les_joueurs[ma_couleur] #les_joueurs est un dico : {"R": {dico_du_joueur},
                                    #                           "B": {dico_du_joueur},
                                    #                             ...}

def score_cout_simulee_direction(le_plateau,joueur,direction,distance_max):
    """Simule selon une direction, l'action de peindre et donne le nombre de points gagnés (=de cases repeintes) et le cout de cette action en points de réserve du joueur

    Args:
        le_plateau (dict): le plateau
        joueur (dict): mon joueur
        direction (str): une direction
        distance_max (int): la distance max 

    Returns:
        tuple: (score,cout)
    """    
    pos_joueur = joueur["pos"] 
    ma_couleur = joueur["couleur"]
    ma_reserve = joueur["reserve"]
    mon_objet = joueur["objet"]
    simul = True

    if mon_objet==const.PISTOLET:
        peindre_murs = True
    else:
        peindre_murs = False

    dict_simulation = plateau.peindre(le_plateau, pos_joueur, direction, ma_couleur, ma_reserve, distance_max, peindre_murs, simul)

    return (dict_simulation["nb_repeintes"],dict_simulation["cout"])

def meilleure_direction_peinture(le_plateau,joueur,distance_max):
    cout = None
    score = 0
    pos_joueur = joueur['pos']
    best_direct = 'X' #au départ, aucune direction n'est choisie, pas de peinture
    d_possibles = plateau.directions_possibles(le_plateau,pos_joueur)

    for direction in d_possibles:
        score_d,cout_d = score_cout_simulee_direction(le_plateau,joueur,direction,distance_max)

        if score_d > score:
            score=score_d
            cout=cout_d  
            best_direct=direction

        elif score == score_d :
            if cout is None or cout_d<cout:
                cout = cout_d
                best_direct=direction

    return best_direct


def plateau_apres_peinture(le_plateau,le_joueur,direction,distance_max): #A utiliser pour calculer le prochain déplacement selon la peinture que l'on vient de faire
    """Prends le plateau original, le copie et modifie cette copie selon l'action de peinture qui va être effectuée

    Args:
        le_plateau (dict): le plateau qui va être copié
        le_joueur (dict): un joueur
        direction (str): la direction dans laquelle on doit peindre
        distance_max (int): la distance max à laquelle on va peindre

    Returns:
        tuple: plateau2,reserve2,res
    """    

    plateau2 = copy.deepcopy(le_plateau)

    if le_joueur['objet']==const.PISTOLET:
        peindre_murs = True
    else:
        peindre_murs=False

    res = plateau.peindre(plateau2,le_joueur['pos'],direction,le_joueur['couleur'],le_joueur['reserve'],distance_max,peindre_murs,False)
    #res est un dictionnaire de type {"cout": ...,"nb_repeintes": ..., "nb_murs_repeints": ...,"joueurs_touches": ...} obtenu grâce à plateau.peindre(.......)
    reserve2 = le_joueur['reserve'] - res['cout']

    return (plateau2,reserve2,res)
#Pour meilleure_direction_deplacement je ne me base que sur le score max que l'on va obtenir en peignant
#Il faudra plus tard prendre en compte les autres cas : si il y a des objets proches, selon notre réserve etc...

#Ici, le meilleur déplacement est celui qui permet de peindre le plus de cases + gérer les autres cas
def meilleure_direction_deplacement(le_plateau,le_joueur,direction_peinture,distance_max): #IL FAUT EFFECTUER LES PREDICTIONS EN PRENANT COMPTE DES CASES QUE LON VIENT DE PEINDRE
    
    le_plateau2,reserve2, _ = plateau_apres_peinture(le_plateau,le_joueur,direction_peinture,distance_max)
    #on récupère une copie du plateau avec les cases coloriées selon notre choix de direction de peinture, et la reserve après cette peinture

    pos_joueur = le_joueur["pos"]
    d_possibles = plateau.directions_possibles(le_plateau2,le_joueur['pos'])
    
    best_score_prochain = 0
    prochain_cout=None
    prochain_deplacement = None

    for direction in d_possibles: #il pourrait être intéressant d'élargir la simulation à toutes les cases pour calculer exactement la trajectoire qui nous fera gagner
        nouvelle_pos = pos_joueur[0] + plateau.INC_DIRECTION[direction][0],pos_joueur[1]+plateau.INC_DIRECTION[direction][1]
        
        joueur_simule = joueur.Joueur(
            le_joueur['couleur'],
            le_joueur['nom'],
            reserve2, #on prend en compte la réserve après la peinture
            le_joueur["surface"],
            le_joueur["points"],
            nouvelle_pos,
            le_joueur["objet"],
            le_joueur["duree_objet"]
            )

        prochaine_direc_a_peindre = meilleure_direction_peinture(le_plateau2,joueur_simule,distance_max)
        prochain_best_score_simule, prochain_cout_simule = score_cout_simulee_direction(le_plateau2,joueur_simule,prochaine_direc_a_peindre,distance_max)

        if prochain_best_score_simule>best_score_prochain:
            best_score_prochain= prochain_best_score_simule
            prochain_cout = prochain_cout_simule
            prochain_deplacement=direction
        
        elif prochain_best_score_simule==best_score_prochain :
            if prochain_cout is None or prochain_cout_simule<prochain_cout:
                best_score_prochain= prochain_best_score_simule
                prochain_cout = prochain_cout_simule
                prochain_deplacement=direction
    
    if best_score_prochain==0: #ex si on est entouré de cases déjà peintes par notre couleur
        return random.choice("NSEO") #SUPPRIMER CETTE LIGNE ET PENSER COMMENT GERER CES CAS LA SELON L'ETAT DU PLATEAU ET DE LA RESERVE

    return prochain_deplacement

def alarme_reserve(joueur):
    """Vérifie si la réseve du joueur va bientôt s'épuiser

    Args:
        joueur (dico): un joueur, ex de joueur :{'couleur':..., 'nom':..., 'reserve' :... }

    Returns:
        bool: True, si la réserve doit être remplie rapidement, False sinon
    """    
    if joueur["reserve"] <= 10:
        return True
    return False


def agir_bombe(plateau,joueur):
    pass

def agir_bouclier(plateau,joueur):
    pass

def agir_pistolet(plateau,joueur):
    pass

def action_selon_objet(plateau,joueur):
    #faire attention à quand appeler cette fonction
    if joueur["objet"]==const.BOMBE:
        agir_bombe(plateau,joueur)

    elif joueur["objet"]==const.BOUCLIER:
        agir_bouclier(plateau,joueur)

    elif joueur["objet"]==const.PISTOLET:
        agir_pistolet(plateau,joueur)

def attaque_judicieuse(plateau,joueur):
    #faire des prédictions sur le coûts des attaques que l'on prévoit de faire
    pass

def direction_plus_zones_vides(plateau,joueur):
    
    pass



def mon_IA(ma_couleur,carac_jeu, le_plateau, les_joueurs):
    """ Cette fonction permet de calculer les deux actions du joueur de couleur ma_couleur
        en fonction de l'état du jeu décrit par les paramètres. 
        Le premier caractère est parmi XSNOE X indique pas de peinture et les autres
        caractères indique la direction où peindre (Nord, Sud, Est ou Ouest)
        Le deuxième caractère est parmi SNOE indiquant la direction où se déplacer.

    Args:
        ma_couleur (str): un caractère en majuscule indiquant la couleur du joueur
        carac_jeu (dict)): un dictionnaire donnant les valeurs des caractéristiques du jeu:
             duree_actuelle, duree_totale, reserve_initiale, duree_obj, penalite, bonus_touche,
             bonus_recharge, bonus_objet et distance_max,
        le_plateau (dict): l'état du plateau actuel sous la forme décrite dans plateau.py
        les_joueurs (list[joueur]): la liste des joueurs avec leurs caractéristiques utilisant l'API
         joueur.py

    Returns:
        str: une chaine de deux caractères en majuscules indiquant la direction de peinture
            et la direction de déplacement
    """
    mon_joueur = trouver_mon_joueur(ma_couleur,les_joueurs)
    direction_peinture =  meilleure_direction_peinture(le_plateau,mon_joueur,carac_jeu["distance_max"])
    direction_deplacement = meilleure_direction_deplacement(le_plateau,mon_joueur,direction_peinture,carac_jeu["distance_max"])

    return direction_peinture+direction_deplacement
    # IA complètement aléatoire
    #return random.choice("XNSOE")+random.choice("NSEO")

if __name__=="__main__":
    noms_caracteristiques=["duree_actuelle","duree_totale","reserve_initiale","duree_obj","penalite","bonus_touche",
            "bonus_recharge","bonus_objet","distance_max"]
    parser = argparse.ArgumentParser()  
    parser.add_argument("--equipe", dest="nom_equipe", help="nom de l'équipe", type=str, default='Non fournie')
    parser.add_argument("--serveur", dest="serveur", help="serveur de jeu", type=str, default='localhost')
    parser.add_argument("--port", dest="port", help="port de connexion", type=int, default=1111)
    
    args = parser.parse_args()
    le_client=client.ClientCyber()
    le_client.creer_socket(args.serveur,args.port)
    le_client.enregistrement(args.nom_equipe,"joueur")
    ok=True
    while ok:
        ok,id_joueur,le_jeu=le_client.  prochaine_commande()
        if ok:
            val_carac_jeu,etat_plateau,les_joueurs=le_jeu.split("--------------------\n")
            joueurs={}
            for ligne in les_joueurs[:-1].split('\n'):
                lejoueur=joueur.joueur_from_str(ligne)
                joueurs[joueur.get_couleur(lejoueur)]=lejoueur
            le_plateau=plateau.Plateau(etat_plateau)
            val_carac=val_carac_jeu.split(";")
            carac_jeu={}
            for i in range(len(noms_caracteristiques)):
                carac_jeu[noms_caracteristiques[i]]=int(val_carac[i])
    
            actions_joueur=mon_IA(id_joueur,carac_jeu,le_plateau,joueurs)
            le_client.envoyer_commande_client(actions_joueur)
            # le_client.afficher_msg("sa reponse  envoyée "+str(id_joueur)+args.nom_equipe)
    le_client.afficher_msg("terminé")
