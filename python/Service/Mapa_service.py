import folium
from folium.plugins import MarkerCluster
from Models.Localizacao import Localizacao
from Models.Loja import Loja


class MapaService:
    @staticmethod
    def gerar_mapa_lojas():
        # Consulta ao PostgreSQL trazendo apenas lojas ativas e carregando a localização atrelada
        lojas = Loja.query.filter_by(status='Ativa').join(Localizacao).all()
        
        if not lojas or not any(loja.localizacao for loja in lojas):
            return None

        # Inicializa o mapa centralizado na coordenada da primeira loja válida
        primeira_loja = next(loja for loja in lojas if loja.localizacao)
        mapa = folium.Map(
            location=[primeira_loja.localizacao.latitude, primeira_loja.localizacao.longitude], 
            zoom_start=11
        )
        
        cluster = MarkerCluster().add_to(mapa)

        # Loop pelas lojas utilizando a relação 'loja.localizacao'
        for loja in lojas:
            if idx_loc := loja.localizacao:
                # LGPD: Montamos um popup estritamente institucional
                # Dados pessoais de gerentes ou faturamento detalhado ficam de fora do HTML final
                popup_conteudo = f"""
                <div style="font-family: Arial, sans-serif; size: 13px;">
                    <h4 style="margin: 0 0 5px 0; color: #1a73e8;">{loja.nome_fantasia}</h4>
                    <b>Cód. Corporativo:</b> {loja.codigo_corporativo}<br>
                    <b>Região:</b> {idx_loc.bairro} - {idx_loc.cidade}<br>
                    <span style="color: green;">● Operação Ativa</span>
                </div>
                """
                
                folium.Marker(
                    location=[idx_loc.latitude, idx_loc.longitude],
                    popup=folium.Popup(popup_conteudo, max_width=300),
                    tooltip=loja.nome_fantasia,
                    icon=folium.Icon(color="blue", icon="shopping-cart", prefix="fa")
                ).add_to(cluster)

        # Retorna o HTML estruturado direto da memória RAM para a rota do Flask
        return mapa._repr_html_()