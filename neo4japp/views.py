import osmnx as ox
import networkx as nx
import folium
from django.shortcuts import render

from neo4japp.neo4j import Neo4jConnection


def display_mapHome(request):
    # Coordonnées du point de départ pour la carte vide
    start_point = (0, 0)
    # Générer une carte vide
    m = folium.Map(location=start_point, zoom_start=13)

    # Convertir la carte en HTML
    html_map = m._repr_html_()

    # Renvoyer la carte vide à afficher
    return render(request, 'map_home.html', {'html_map': html_map})

def display_map(request):
    if request.method == 'POST':
        latitude = float(request.POST.get('latitude', 0))  # Défaut à 0 si non fourni
        longitude = float(request.POST.get('longitude', 0))  # Défaut à 0 si non fourni
        ville = request.POST.get('ville')
        category = request.POST.get('category')
        print(ville, category)

        # Connexion à Neo4j
        conn = Neo4jConnection("bolt://localhost:7687", "neo4j", "12345678")

        try:
            # Utiliser le nom de la ville fourni pour obtenir les données OSM
            gdf = ox.geocode_to_gdf(f"{ville}, Maroc")

            # Obtenir les équipements dans la ville en utilisant des tags spécifiques
            tags = {'amenity': category}
            categories = ox.geometries_from_place(ville, tags)

            # Créer le graphe routier pour la ville
            G = ox.graph_from_place(ville, network_type='drive')

            # Trouver le nœud le plus proche du point de départ
            start_node = ox.distance.nearest_nodes(G, longitude, latitude)

            # Trouver les nœuds les plus proches des équipements
            nodes = [ox.distance.nearest_nodes(G, point.x, point.y) for point in categories.geometry]

            # Calculer les chemins les plus courts du point de départ aux équipements
            lengths = nx.single_source_dijkstra_path_length(G, start_node)

            # Trouver le nœud d'équipement le plus proche
            closest_node = min(nodes, key=lambda node: lengths.get(node, float('inf')))
            closest_distance = lengths[closest_node]

            # Trouver le chemin le plus court vers l'équipement le plus proche
            shortest_path = nx.shortest_path(G, start_node, closest_node, weight='length')
            route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in shortest_path]

            # Stocker la ville dans Neo4j
            conn.create_node("City", {"name": ville})

            # Stocker les équipements et les relations dans Neo4j
            for point in categories.geometry:
                amenity_name = f"{category.capitalize()} at ({point.y}, {point.x})"
                conn.create_node("Amenity", {"name": amenity_name, "category": category, "latitude": point.y, "longitude": point.x})
                conn.create_relationship("City", {"name": ville}, "Amenity", {"name": amenity_name}, "HAS_AMENITY")

            # Créer une carte Folium
            m = folium.Map(location=(latitude, longitude), zoom_start=13)

            # Ajouter la géométrie de la ville à la carte
            folium.GeoJson(gdf.geometry).add_to(m)

            # Ajouter des marqueurs pour chaque équipement dans la ville
            for point in categories.geometry:
                coords = (point.y, point.x)
                folium.Marker(location=coords, popup=category.capitalize(), icon=folium.Icon(color='blue')).add_to(m)

            # Ajouter un marqueur pour le point de départ
            folium.Marker(location=(latitude, longitude), popup='Point de départ', icon=folium.Icon(color='red')).add_to(m)

            # Ajouter un marqueur pour l'équipement le plus proche
            closest_hotel_geom = (G.nodes[closest_node]['y'], G.nodes[closest_node]['x'])
            folium.Marker(location=closest_hotel_geom, popup='Le plus proche ' + category.capitalize(), icon=folium.Icon(color='green')).add_to(m)

            # Tracer le chemin le plus court vers l'équipement le plus proche
            folium.PolyLine(route_coords, color='blue', weight=2.5, opacity=1).add_to(m)

            # Obtenir le contenu HTML de la carte Folium
            html_map = m._repr_html_()

            # Message de succès
            success_message = "Les données ont été stockées avec succès dans Neo4j."

        except Exception as e:
            success_message = f"Une erreur s'est produite : {str(e)}"

        finally:
            # Fermer la connexion à Neo4j
            conn.close()

        return render(request, 'map.html', {'html_map': html_map, 'success_message': success_message})

    return render(request, 'map.html')