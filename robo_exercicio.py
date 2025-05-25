# -*- coding: utf-8 -*-
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import json
import time
import multiprocessing
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
import seaborn as sns
from collections import defaultdict

# =====================================================================
# PARTE 1: ESTRUTURA DA SIMULAÇÃO (NÃO MODIFICAR)
# Esta parte contém a estrutura básica da simulação, incluindo o ambiente,
# o robô e a visualização. Não é recomendado modificar esta parte.
# =====================================================================


class Ambiente:
    def __init__(self, largura=800, altura=600, num_obstaculos=5, num_recursos=5):
        self.largura = largura
        self.altura = altura
        self.obstaculos = self.gerar_obstaculos(num_obstaculos)
        self.recursos = self.gerar_recursos(num_recursos)
        self.tempo = 0
        self.max_tempo = 1000  # Tempo máximo de simulação
        self.meta = self.gerar_meta()  # Adicionando a meta
        self.meta_atingida = False  # Flag para controlar se a meta foi atingida

    def gerar_obstaculos(self, num_obstaculos):
        obstaculos = []
        for _ in range(num_obstaculos):
            x = random.randint(50, self.largura - 50)
            y = random.randint(50, self.altura - 50)
            largura = random.randint(20, 100)
            altura = random.randint(20, 100)
            obstaculos.append({
                'x': x,
                'y': y,
                'largura': largura,
                'altura': altura
            })
        return obstaculos

    def gerar_recursos(self, num_recursos):
        recursos = []
        for _ in range(num_recursos):
            x = random.randint(20, self.largura - 20)
            y = random.randint(20, self.altura - 20)
            recursos.append({
                'x': x,
                'y': y,
                'coletado': False
            })
        return recursos

    def gerar_meta(self):
        # Gerar a meta em uma posição segura, longe dos obstáculos
        max_tentativas = 100
        margem = 50  # Margem das bordas

        for _ in range(max_tentativas):
            x = random.randint(margem, self.largura - margem)
            y = random.randint(margem, self.altura - margem)

            # Verificar se a posição está longe o suficiente dos obstáculos
            posicao_segura = True
            for obstaculo in self.obstaculos:
                # Calcular a distância até o obstáculo mais próximo
                dist_x = max(obstaculo['x'] - x, 0, x -
                             (obstaculo['x'] + obstaculo['largura']))
                dist_y = max(obstaculo['y'] - y, 0, y -
                             (obstaculo['y'] + obstaculo['altura']))
                dist = np.sqrt(dist_x**2 + dist_y**2)

                if dist < 50:  # 50 pixels de margem extra
                    posicao_segura = False
                    break

            if posicao_segura:
                return {
                    'x': x,
                    'y': y,
                    'raio': 30  # Raio da meta
                }

        # Se não encontrar uma posição segura, retorna o centro
        return {
            'x': self.largura // 2,
            'y': self.altura // 2,
            'raio': 30
        }

    def verificar_colisao(self, x, y, raio):
        # Verificar colisão com as bordas
        if x - raio < 0 or x + raio > self.largura or y - raio < 0 or y + raio > self.altura:
            return True

        # Verificar colisão com obstáculos
        for obstaculo in self.obstaculos:
            if (x + raio > obstaculo['x'] and
                x - raio < obstaculo['x'] + obstaculo['largura'] and
                y + raio > obstaculo['y'] and
                    y - raio < obstaculo['y'] + obstaculo['altura']):
                return True

        return False

    def verificar_coleta_recursos(self, x, y, raio):
        recursos_coletados = 0
        for recurso in self.recursos:
            if not recurso['coletado']:
                distancia = np.sqrt(
                    (x - recurso['x'])**2 + (y - recurso['y'])**2)
                if distancia < raio + 10:  # 10 é o raio do recurso
                    recurso['coletado'] = True
                    recursos_coletados += 1
        return recursos_coletados

    def verificar_atingir_meta(self, x, y, raio):
        if not self.meta_atingida:
            distancia = np.sqrt(
                (x - self.meta['x'])**2 + (y - self.meta['y'])**2)
            if distancia < raio + self.meta['raio']:
                self.meta_atingida = True
                return True
        return False

    def reset(self):
        self.tempo = 0
        for recurso in self.recursos:
            recurso['coletado'] = False
        self.meta_atingida = False
        return self.get_estado()

    def get_estado(self):
        return {
            'tempo': self.tempo,
            'recursos_coletados': sum(1 for r in self.recursos if r['coletado']),
            'recursos_restantes': sum(1 for r in self.recursos if not r['coletado']),
            'meta_atingida': self.meta_atingida
        }

    def passo(self):
        self.tempo += 1
        return self.tempo >= self.max_tempo

    def posicao_segura(self, raio_robo=15):
        """Encontra uma posição segura para o robô, longe dos obstáculos"""
        max_tentativas = 100
        margem = 50  # Margem das bordas

        for _ in range(max_tentativas):
            x = random.randint(margem, self.largura - margem)
            y = random.randint(margem, self.altura - margem)

            # Verificar se a posição está longe o suficiente dos obstáculos
            posicao_segura = True
            for obstaculo in self.obstaculos:
                # Calcular a distância até o obstáculo mais próximo
                dist_x = max(obstaculo['x'] - x, 0, x -
                             (obstaculo['x'] + obstaculo['largura']))
                dist_y = max(obstaculo['y'] - y, 0, y -
                             (obstaculo['y'] + obstaculo['altura']))
                dist = np.sqrt(dist_x**2 + dist_y**2)

                if dist < raio_robo + 20:  # 20 pixels de margem extra
                    posicao_segura = False
                    break

            if posicao_segura:
                return x, y

        # Se não encontrar uma posição segura, retorna o centro
        return self.largura // 2, self.altura // 2


class Robo:
    def __init__(self, x, y, raio=15):
        self.x = x
        self.y = y
        self.raio = raio
        self.angulo = 0  # em radianos
        self.velocidade = 0
        self.energia = 100
        self.recursos_coletados = 0
        self.colisoes = 0
        self.distancia_percorrida = 0
        self.tempo_parado = 0  # Novo: contador de tempo parado
        self.ultima_posicao = (x, y)  # Novo: última posição conhecida
        self.meta_atingida = False  # Novo: flag para controlar se a meta foi atingida

    def reset(self, x, y):
        self.x = x
        self.y = y
        self.angulo = 0
        self.velocidade = 0
        self.energia = 100
        self.recursos_coletados = 0
        self.colisoes = 0
        self.distancia_percorrida = 0
        self.tempo_parado = 0
        self.ultima_posicao = (x, y)
        self.meta_atingida = False

    def mover(self, aceleracao, rotacao, ambiente):
        # Atualizar ângulo
        self.angulo += rotacao

        # Verificar se o robô está parado
        distancia_movimento = np.sqrt(
            (self.x - self.ultima_posicao[0])**2 + (self.y - self.ultima_posicao[1])**2)
        if distancia_movimento < 0.1:  # Se moveu menos de 0.1 unidades
            self.tempo_parado += 1
            # Forçar movimento após ficar parado por muito tempo
            if self.tempo_parado > 5:  # Após 5 passos parado
                aceleracao = max(0.2, aceleracao)  # Força aceleração mínima
                # Pequena rotação aleatória
                rotacao = random.uniform(-0.2, 0.2)
        else:
            self.tempo_parado = 0

        # Atualizar velocidade
        self.velocidade += aceleracao
        # Velocidade mínima de 0.1
        self.velocidade = max(0.1, min(5, self.velocidade))

        # Calcular nova posição
        novo_x = self.x + self.velocidade * np.cos(self.angulo)
        novo_y = self.y + self.velocidade * np.sin(self.angulo)

        # Verificar colisão
        if ambiente.verificar_colisao(novo_x, novo_y, self.raio):
            self.colisoes += 1
            self.velocidade = 0.1  # Mantém velocidade mínima mesmo após colisão
            # Tenta uma direção diferente após colisão
            self.angulo += random.uniform(-np.pi/4, np.pi/4)
        else:
            # Atualizar posição
            self.distancia_percorrida += np.sqrt(
                (novo_x - self.x)**2 + (novo_y - self.y)**2)
            self.x = novo_x
            self.y = novo_y

        # Atualizar última posição conhecida
        self.ultima_posicao = (self.x, self.y)

        # Verificar coleta de recursos
        recursos_coletados = ambiente.verificar_coleta_recursos(
            self.x, self.y, self.raio)
        self.recursos_coletados += recursos_coletados

        # Verificar se atingiu a meta
        if not self.meta_atingida and ambiente.verificar_atingir_meta(self.x, self.y, self.raio):
            self.meta_atingida = True
            # Recuperar energia ao atingir a meta
            self.energia = min(100, self.energia + 50)

        # Consumir energia
        self.energia -= 0.1 + 0.05 * self.velocidade + 0.1 * abs(rotacao)
        self.energia = max(0, self.energia)

        # Recuperar energia ao coletar recursos
        if recursos_coletados > 0:
            self.energia = min(100, self.energia + 20 * recursos_coletados)

        return self.energia <= 0

    def get_sensores(self, ambiente):
        # Distância até o recurso mais próximo
        dist_recurso = float('inf')
        for recurso in ambiente.recursos:
            if not recurso['coletado']:
                dist = np.sqrt(
                    (self.x - recurso['x'])**2 + (self.y - recurso['y'])**2)
                dist_recurso = min(dist_recurso, dist)

        # Distância até o obstáculo mais próximo
        dist_obstaculo = float('inf')
        for obstaculo in ambiente.obstaculos:
            # Simplificação: considerar apenas a distância até o centro do obstáculo
            centro_x = obstaculo['x'] + obstaculo['largura'] / 2
            centro_y = obstaculo['y'] + obstaculo['altura'] / 2
            dist = np.sqrt((self.x - centro_x)**2 + (self.y - centro_y)**2)
            dist_obstaculo = min(dist_obstaculo, dist)

        # Distância até a meta
        dist_meta = np.sqrt(
            (self.x - ambiente.meta['x'])**2 + (self.y - ambiente.meta['y'])**2)

        # Ângulo até o recurso mais próximo
        angulo_recurso = 0
        if dist_recurso < float('inf'):
            for recurso in ambiente.recursos:
                if not recurso['coletado']:
                    dx = recurso['x'] - self.x
                    dy = recurso['y'] - self.y
                    angulo = np.arctan2(dy, dx)
                    angulo_recurso = angulo - self.angulo
                    # Normalizar para [-pi, pi]
                    while angulo_recurso > np.pi:
                        angulo_recurso -= 2 * np.pi
                    while angulo_recurso < -np.pi:
                        angulo_recurso += 2 * np.pi
                    break

        # Ângulo até a meta
        dx_meta = ambiente.meta['x'] - self.x
        dy_meta = ambiente.meta['y'] - self.y
        angulo_meta = np.arctan2(dy_meta, dx_meta) - self.angulo
        # Normalizar para [-pi, pi]
        while angulo_meta > np.pi:
            angulo_meta -= 2 * np.pi
        while angulo_meta < -np.pi:
            angulo_meta += 2 * np.pi

        return {
            'dist_recurso': dist_recurso,
            'dist_obstaculo': dist_obstaculo,
            'dist_meta': dist_meta,
            'angulo_recurso': angulo_recurso,
            'angulo_meta': angulo_meta,
            'energia': self.energia,
            'velocidade': self.velocidade,
            'meta_atingida': self.meta_atingida
        }


class Simulador:
    def __init__(self, ambiente, robo, individuo):
        self.ambiente = ambiente
        self.robo = robo
        self.individuo = individuo
        self.frames = []

        # Configurar matplotlib para melhor visualização
        plt.style.use('default')  # Usar estilo padrão
        plt.ion()  # Modo interativo
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.ax.set_xlim(0, ambiente.largura)
        self.ax.set_ylim(0, ambiente.altura)
        self.ax.set_title(
            "Simulador de Robô com Programação Genética", fontsize=14)
        self.ax.set_xlabel("X", fontsize=12)
        self.ax.set_ylabel("Y", fontsize=12)
        self.ax.grid(True, linestyle='--', alpha=0.7)

    def simular(self):
        self.ambiente.reset()
        # Encontrar uma posição segura para o robô
        x_inicial, y_inicial = self.ambiente.posicao_segura(self.robo.raio)
        self.robo.reset(x_inicial, y_inicial)
        self.frames = []

        # Limpar a figura atual
        self.ax.clear()
        self.ax.set_xlim(0, self.ambiente.largura)
        self.ax.set_ylim(0, self.ambiente.altura)
        self.ax.set_title(
            "Simulador de Robô com Programação Genética", fontsize=14)
        self.ax.set_xlabel("X", fontsize=12)
        self.ax.set_ylabel("Y", fontsize=12)
        self.ax.grid(True, linestyle='--', alpha=0.7)

        # Desenhar obstáculos (estáticos)
        for obstaculo in self.ambiente.obstaculos:
            rect = patches.Rectangle(
                (obstaculo['x'], obstaculo['y']),
                obstaculo['largura'],
                obstaculo['altura'],
                linewidth=1,
                edgecolor='black',
                facecolor='#FF9999',  # Vermelho claro
                alpha=0.7
            )
            self.ax.add_patch(rect)

        # Desenhar recursos (estáticos)
        for recurso in self.ambiente.recursos:
            if not recurso['coletado']:
                circ = patches.Circle(
                    (recurso['x'], recurso['y']),
                    10,
                    linewidth=1,
                    edgecolor='black',
                    facecolor='#99FF99',  # Verde claro
                    alpha=0.8
                )
                self.ax.add_patch(circ)

        # Desenhar a meta
        meta_circ = patches.Circle(
            (self.ambiente.meta['x'], self.ambiente.meta['y']),
            self.ambiente.meta['raio'],
            linewidth=2,
            edgecolor='black',
            facecolor='#FFFF00',  # Amarelo
            alpha=0.8
        )
        self.ax.add_patch(meta_circ)

        # Criar objetos para o robô e direção (serão atualizados)
        robo_circ = patches.Circle(
            (self.robo.x, self.robo.y),
            self.robo.raio,
            linewidth=1,
            edgecolor='black',
            facecolor='#9999FF',  # Azul claro
            alpha=0.8
        )
        self.ax.add_patch(robo_circ)

        # Criar texto para informações
        info_text = self.ax.text(
            10, self.ambiente.altura - 50,  # Alterado de 10 para 50 para descer a legenda
            "",
            fontsize=12,
            bbox=dict(facecolor='white', alpha=0.8,
                      edgecolor='gray', boxstyle='round,pad=0.5')
        )

        # Atualizar a figura
        plt.draw()
        plt.pause(0.01)

        try:
            while True:
                # Obter sensores
                sensores = self.robo.get_sensores(self.ambiente)

                # Avaliar árvores de decisão
                aceleracao = self.individuo.avaliar(sensores, 'aceleracao')
                rotacao = self.individuo.avaliar(sensores, 'rotacao')

                # Limitar valores
                aceleracao = max(-1, min(1, aceleracao))
                rotacao = max(-0.5, min(0.5, rotacao))

                # Mover robô
                sem_energia = self.robo.mover(
                    aceleracao, rotacao, self.ambiente)

                # Atualizar visualização em tempo real
                self.ax.clear()
                self.ax.set_xlim(0, self.ambiente.largura)
                self.ax.set_ylim(0, self.ambiente.altura)
                self.ax.set_title(
                    "Simulador de Robô com Programação Genética", fontsize=14)
                self.ax.set_xlabel("X", fontsize=12)
                self.ax.set_ylabel("Y", fontsize=12)
                self.ax.grid(True, linestyle='--', alpha=0.7)

                # Desenhar obstáculos
                for obstaculo in self.ambiente.obstaculos:
                    rect = patches.Rectangle(
                        (obstaculo['x'], obstaculo['y']),
                        obstaculo['largura'],
                        obstaculo['altura'],
                        linewidth=1,
                        edgecolor='black',
                        facecolor='#FF9999',
                        alpha=0.7
                    )
                    self.ax.add_patch(rect)

                # Desenhar recursos
                for recurso in self.ambiente.recursos:
                    if not recurso['coletado']:
                        circ = patches.Circle(
                            (recurso['x'], recurso['y']),
                            10,
                            linewidth=1,
                            edgecolor='black',
                            facecolor='#99FF99',
                            alpha=0.8
                        )
                        self.ax.add_patch(circ)

                # Desenhar a meta
                meta_circ = patches.Circle(
                    (self.ambiente.meta['x'], self.ambiente.meta['y']),
                    self.ambiente.meta['raio'],
                    linewidth=2,
                    edgecolor='black',
                    facecolor='#FFFF00',  # Amarelo
                    alpha=0.8
                )
                self.ax.add_patch(meta_circ)

                # Desenhar robô
                robo_circ = patches.Circle(
                    (self.robo.x, self.robo.y),
                    self.robo.raio,
                    linewidth=1,
                    edgecolor='black',
                    facecolor='#9999FF',
                    alpha=0.8
                )
                self.ax.add_patch(robo_circ)

                # Desenhar direção do robô
                direcao_x = self.robo.x + self.robo.raio * \
                    np.cos(self.robo.angulo)
                direcao_y = self.robo.y + self.robo.raio * \
                    np.sin(self.robo.angulo)
                self.ax.plot([self.robo.x, direcao_x], [
                             self.robo.y, direcao_y], 'r-', linewidth=2)

                # Adicionar informações
                info_text = self.ax.text(
                    10, self.ambiente.altura - 50,  # Alterado de 10 para 50 para descer a legenda
                    f"Tempo: {self.ambiente.tempo}\n"
                    f"Recursos: {self.robo.recursos_coletados}\n"
                    f"Energia: {self.robo.energia:.1f}\n"
                    f"Colisões: {self.robo.colisoes}\n"
                    f"Distância: {self.robo.distancia_percorrida:.1f}\n"
                    f"Meta atingida: {'Sim' if self.robo.meta_atingida else 'Não'}",
                    fontsize=12,
                    bbox=dict(facecolor='white', alpha=0.8,
                              edgecolor='gray', boxstyle='round,pad=0.5')
                )

                # Atualizar a figura
                plt.draw()
                plt.pause(0.05)

                # Verificar fim da simulação
                if sem_energia or self.ambiente.passo():
                    break

            # Manter a figura aberta até que o usuário a feche
            plt.ioff()
            plt.show()

        except KeyboardInterrupt:
            plt.close('all')

        return self.frames

    def animar(self):
        # Desativar o modo interativo antes de criar a animação
        plt.ioff()

        # Criar a animação
        anim = animation.FuncAnimation(
            self.fig, self.atualizar_frame,
            frames=len(self.frames),
            interval=50,
            blit=True,
            repeat=True  # Permitir que a animação repita
        )

        # Mostrar a animação e manter a janela aberta
        plt.show(block=True)

    def atualizar_frame(self, frame_idx):
        return self.frames[frame_idx]

# =====================================================================
# PARTE 2: ALGORITMO GENÉTICO (PARA O VOCÊ MODIFICAR)
# Esta parte contém a implementação do algoritmo genético.
# Deve modificar os parâmetros e a lógica para melhorar o desempenho.
# =====================================================================
class IndividuoPG:
    def __init__(self, profundidade=5):
        self.profundidade = profundidade
        self.arvore_aceleracao = self.criar_arvore(profundidade)
        self.arvore_rotacao = self.criar_arvore(profundidade)
        self.fitness = 0
        self.ultima_colisao = False  # Novo: controla se houve colisão no último passo

    def criar_arvore(self, profundidade):
        if profundidade == 0:
            return self.criar_folha()

        operador = random.choice(['+', '-', '*', '/', 'max', 'min', 'abs'])
        if operador in ['+', '-', '*', '/', 'max', 'min']:
            return {
                'tipo': 'operador',
                'operador': operador,
                'esquerda': self.criar_arvore(profundidade - 1),
                'direita': self.criar_arvore(profundidade - 1)
            }
        elif operador == 'abs':
            return {
                'tipo': 'operador',
                'operador': operador,
                'esquerda': self.criar_arvore(profundidade - 1),
                'direita': None
            }

    def criar_folha(self):
        terminal = random.choices(
            ['dist_recurso', 'angulo_recurso', 'dist_meta', 'angulo_meta',
             'dist_obstaculo', 'energia', 'velocidade', 'meta_atingida', 'constante'],
            weights=[10, 10, 5, 5, 12, 4, 4, 2, 3],
            k=1
        )[0]

        if terminal == 'constante':
            return {'tipo': 'folha', 'valor': random.uniform(-5, 5)}
        else:
            return {'tipo': 'folha', 'variavel': terminal}

    def avaliar(self, sensores, tipo='aceleracao'):
        arvore = self.arvore_aceleracao if tipo == 'aceleracao' else self.arvore_rotacao
        resultado = self.avaliar_no(arvore, sensores)

        recursos_restantes = sensores.get('recursos_restantes', 0)
        dist_obstaculo = sensores.get('dist_obstaculo', float('inf'))
        angulo_meta = sensores.get('angulo_meta', 0)
        angulo_recurso = sensores.get('angulo_recurso', 0)
        velocidade = sensores.get('velocidade', 0)
        dist_recurso = sensores.get('dist_recurso', float('inf'))

        # Lógica de evasão de obstáculos aprimorada
        if dist_obstaculo < 150:  # Aumentado o alcance de detecção
            # Calcula a distância de segurança baseada na velocidade
            distancia_seguranca = max(50, velocidade * 30)  # Ajusta dinamicamente
            
            if dist_obstaculo < distancia_seguranca:
                if tipo == 'rotacao':
                    # Calcula o ângulo de evasão baseado na posição do obstáculo
                    angulo_evasao = angulo_recurso + np.pi/2  # 90 graus
                    
                    # Ajusta a intensidade da rotação baseado na distância
                    intensidade_rotacao = min(0.4, 0.2 + (distancia_seguranca - dist_obstaculo) / 100)
                    
                    # Normaliza o ângulo para [-pi, pi]
                    while angulo_evasao > np.pi:
                        angulo_evasao -= 2 * np.pi
                    while angulo_evasao < -np.pi:
                        angulo_evasao += 2 * np.pi
                    
                    # Aplica a rotação com intensidade dinâmica
                    resultado = np.sign(angulo_evasao) * intensidade_rotacao
                    
                    # Adiciona uma pequena variação aleatória para evitar ficar preso
                    resultado += random.uniform(-0.05, 0.05)
                    
                elif tipo == 'aceleracao':
                    # Reduz a velocidade de forma mais gradual
                    fator_reducao = min(1.0, dist_obstaculo / distancia_seguranca)
                    velocidade_maxima = 0.3 * fator_reducao
                    resultado = min(resultado, velocidade_maxima)
                    
                    # Se estiver muito próximo, força uma desaceleração
                    if dist_obstaculo < 50:
                        resultado = -0.1  # Pequena desaceleração

        # Lógica de coleta de recursos aprimorada
        if recursos_restantes > 0:
            if tipo == 'rotacao':
                # Se estiver muito próximo de um recurso, ajusta o ângulo para coletá-lo
                if dist_recurso < 50:
                    # Força um alinhamento mais preciso com o recurso
                    resultado = angulo_recurso * 0.8
                else:
                    # Normaliza o ângulo para o recurso
                    angulo_normalizado = angulo_recurso
                    while angulo_normalizado > np.pi:
                        angulo_normalizado -= 2 * np.pi
                    while angulo_normalizado < -np.pi:
                        angulo_normalizado += 2 * np.pi
                    
                    # Aplica uma rotação mais suave e direcionada
                    resultado = angulo_normalizado * 0.5
                    
                    # Adiciona uma pequena variação para evitar oscilações
                    if abs(angulo_normalizado) < 0.2:
                        resultado += random.uniform(-0.1, 0.1)
            
            elif tipo == 'aceleracao':
                # Ajusta a velocidade baseado na distância do recurso
                if dist_recurso < 50:
                    # Mantém velocidade constante quando próximo do recurso
                    resultado = 0.3
                else:
                    # Aumenta a velocidade quando está longe
                    resultado = min(0.8, 0.3 + dist_recurso / 200)

        else:
            if tipo == 'aceleracao':
                resultado += 2.0 / (sensores.get('dist_meta', 1) + 1)
            elif tipo == 'rotacao':
                resultado -= abs(sensores.get('angulo_meta', 0))

        return resultado

    def avaliar_no(self, no, sensores):
        if no is None:
            return 0

        if no['tipo'] == 'folha':
            if 'valor' in no:
                return no['valor']
            if 'variavel' in no:
                return sensores.get(no['variavel'], 0)

        op = no['operador']
        if op == 'abs':
            resultado = abs(self.avaliar_no(no['esquerda'], sensores))
        else:
            esquerda = self.avaliar_no(no.get('esquerda'), sensores)
            direita = self.avaliar_no(no.get('direita'), sensores) if no.get('direita') else 0

            try:
                if op == '+':
                    resultado = esquerda + direita
                elif op == '-':
                    resultado = esquerda - direita
                elif op == '*':
                    resultado = esquerda * direita
                elif op == '/':
                    resultado = esquerda / direita if direita != 0 else 0
                elif op == 'max':
                    resultado = max(esquerda, direita)
                elif op == 'min':
                    resultado = min(esquerda, direita)
                else:
                    resultado = 0
            except:
                resultado = 0

        if resultado != resultado or resultado == float('inf') or resultado == float('-inf'):
            return 0

        return resultado

    def mutacao(self, probabilidade=0.25):
        self.arvore_aceleracao = self._mutacao_no(self.arvore_aceleracao, probabilidade)
        self.arvore_rotacao = self._mutacao_no(self.arvore_rotacao, probabilidade)

    def _mutacao_no(self, no, probabilidade):
        if no is None:
            return self.criar_arvore(2)

        if random.random() < probabilidade:
            return self.criar_arvore(2)

        if no['tipo'] == 'operador':
            no['esquerda'] = self._mutacao_no(no.get('esquerda'), probabilidade)
            if no.get('direita') is not None:
                no['direita'] = self._mutacao_no(no.get('direita'), probabilidade)
        return no

    def crossover(self, outro):
        filho = IndividuoPG(self.profundidade)
        filho.arvore_aceleracao = self._crossover_no(self.arvore_aceleracao, outro.arvore_aceleracao)
        filho.arvore_rotacao = self._crossover_no(self.arvore_rotacao, outro.arvore_rotacao)
        return filho

    def _crossover_no(self, no1, no2):
        if no1 is None:
            return json.loads(json.dumps(no2))
        if no2 is None:
            return json.loads(json.dumps(no1))

        if no1['tipo'] == 'folha' or no2['tipo'] == 'folha':
            return json.loads(json.dumps(random.choice([no1, no2])))

        if no1['operador'] == no2['operador']:
            return {
                'tipo': 'operador',
                'operador': no1['operador'],
                'esquerda': self._crossover_no(no1.get('esquerda'), no2.get('esquerda')),
                'direita': self._crossover_no(no1.get('direita'), no2.get('direita'))
            }

        return json.loads(json.dumps(random.choice([no1, no2])))

    def salvar(self, arquivo):
        with open(arquivo, 'w') as f:
            json.dump({
                'arvore_aceleracao': self.arvore_aceleracao,
                'arvore_rotacao': self.arvore_rotacao
            }, f)

    @classmethod
    def carregar(cls, arquivo):
        with open(arquivo, 'r') as f:
            dados = json.load(f)
        individuo = cls()
        individuo.arvore_aceleracao = dados['arvore_aceleracao']
        individuo.arvore_rotacao = dados['arvore_rotacao']
        return individuo


class MetricasAvaliacao:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.recursos_coletados = 0
        self.tempo_ate_meta = 0
        self.colisoes = 0
        self.energia_final = 0
        self.distancia_percorrida = 0
        self.tempo_parado = 0
        self.angulos_medios = []
        self.velocidades_medias = []
        
    def calcular_metricas(self, robo, ambiente):
        self.recursos_coletados = robo.recursos_coletados
        self.tempo_ate_meta = ambiente.tempo if robo.meta_atingida else float('inf')
        self.colisoes = robo.colisoes
        self.energia_final = robo.energia
        self.distancia_percorrida = robo.distancia_percorrida
        self.tempo_parado = robo.tempo_parado
        
    def get_metricas(self):
        return {
            'recursos_coletados': self.recursos_coletados,
            'tempo_ate_meta': self.tempo_ate_meta,
            'colisoes': self.colisoes,
            'energia_final': self.energia_final,
            'distancia_percorrida': self.distancia_percorrida,
            'tempo_parado': self.tempo_parado,
            'angulo_medio': np.mean(self.angulos_medios) if self.angulos_medios else 0,
            'velocidade_media': np.mean(self.velocidades_medias) if self.velocidades_medias else 0
        }

class EstrategiaMutacao:
    @staticmethod
    def mutacao_padrao(no, probabilidade):
        if random.random() < probabilidade:
            # Criar uma nova árvore com profundidade 2
            return {
                'tipo': 'operador',
                'operador': random.choice(['+', '-', '*', '/', 'max', 'min', 'abs']),
                'esquerda': {
                    'tipo': 'folha',
                    'variavel': random.choice(['dist_recurso', 'angulo_recurso', 'dist_meta', 'angulo_meta',
                                             'dist_obstaculo', 'energia', 'velocidade', 'meta_atingida'])
                },
                'direita': {
                    'tipo': 'folha',
                    'variavel': random.choice(['dist_recurso', 'angulo_recurso', 'dist_meta', 'angulo_meta',
                                             'dist_obstaculo', 'energia', 'velocidade', 'meta_atingida'])
                }
            }
        return no
    
    @staticmethod
    def mutacao_adaptativa(no, probabilidade, fitness):
        # Ajusta probabilidade baseado no fitness
        prob_ajustada = probabilidade * (1 - fitness/10000)
        return EstrategiaMutacao.mutacao_padrao(no, prob_ajustada)
    
    @staticmethod
    def mutacao_estrutural(no, probabilidade):
        if no['tipo'] == 'operador':
            if random.random() < probabilidade:
                # Muda o operador mantendo a estrutura
                no['operador'] = random.choice(['+', '-', '*', '/', 'max', 'min', 'abs'])
            no['esquerda'] = EstrategiaMutacao.mutacao_estrutural(no['esquerda'], probabilidade)
            if no.get('direita'):
                no['direita'] = EstrategiaMutacao.mutacao_estrutural(no['direita'], probabilidade)
        return no

class ProgramacaoGeneticaParalela:
    def __init__(self, tamanho_populacao=40, profundidade=5, num_processos=None):
        self.tamanho_populacao = tamanho_populacao
        self.profundidade = profundidade
        self.num_processos = num_processos or multiprocessing.cpu_count()
        self.populacao = [IndividuoPG(profundidade) for _ in range(tamanho_populacao)]
        self.melhor_individuo = None
        self.melhor_fitness = float('-inf')
        self.historico_fitness = []
        self.metricas = MetricasAvaliacao()
        
    def avaliar_individuo(self, individuo):
        ambiente = Ambiente()
        robo = Robo(ambiente.largura // 2, ambiente.altura // 2)
        fitness = 0
        
        for _ in range(3):
            ambiente.reset()
            robo.reset(ambiente.largura // 2, ambiente.altura // 2)
            self.metricas.reset()
            
            while True:
                sensores = robo.get_sensores(ambiente)
                estado = ambiente.get_estado()
                sensores['recursos_restantes'] = estado['recursos_restantes']
                
                aceleracao = individuo.avaliar(sensores, 'aceleracao')
                rotacao = individuo.avaliar(sensores, 'rotacao')
                
                aceleracao = max(-1, min(1, aceleracao))
                rotacao = max(-0.5, min(0.5, rotacao))
                
                sem_energia = robo.mover(aceleracao, rotacao, ambiente)
                
                if sem_energia or ambiente.passo():
                    break
            
            self.metricas.calcular_metricas(robo, ambiente)
            fitness += self.calcular_fitness(robo, ambiente)
            
        return fitness / 3, self.metricas.get_metricas()
    
    def avaliar_populacao_paralela(self):
        with ProcessPoolExecutor(max_workers=self.num_processos) as executor:
            resultados = list(executor.map(self.avaliar_individuo, self.populacao))
            
        for individuo, (fitness, metricas) in zip(self.populacao, resultados):
            individuo.fitness = fitness
            if fitness > self.melhor_fitness:
                self.melhor_fitness = fitness
                self.melhor_individuo = individuo
                
        return resultados
    
    def calcular_fitness(self, robo, ambiente):
        estado = ambiente.get_estado()
        recursos_nao_coletados = estado['recursos_restantes']
        
        # Penalidade maior para colisões
        fitness = (
            robo.recursos_coletados * 4000 +
            (7000 if (robo.meta_atingida and recursos_nao_coletados == 0) else 0) -
            recursos_nao_coletados * 6000 -
            robo.colisoes * 500 +  # Aumentado de 200 para 500
            robo.energia * 3 +
            robo.distancia_percorrida * 0.2
        )
        
        if recursos_nao_coletados > 0 and robo.meta_atingida:
            fitness -= 8000
            
        return max(1, fitness)
    
    def calcular_metricas_populacao(self):
        metricas = {
            'fitness_medio': np.mean([ind.fitness for ind in self.populacao]),
            'melhor_fitness': self.melhor_fitness,
            'diversidade': self.calcular_diversidade(),
            'taxa_mutacao': 0.25,  # Pode ser ajustado
            'complexidade': self.calcular_complexidade_media()
        }
        return metricas
    
    def calcular_diversidade(self):
        # Calcula a diversidade genética da população
        fitness_values = [ind.fitness for ind in self.populacao]
        return np.std(fitness_values)
    
    def calcular_complexidade_media(self):
        # Calcula a complexidade média das árvores
        complexidades = []
        for ind in self.populacao:
            comp_acel = self.calcular_complexidade_arvore(ind.arvore_aceleracao)
            comp_rot = self.calcular_complexidade_arvore(ind.arvore_rotacao)
            complexidades.append((comp_acel + comp_rot) / 2)
        return np.mean(complexidades)
    
    def calcular_complexidade_arvore(self, no):
        if no is None:
            return 0
        if no['tipo'] == 'folha':
            return 1
        return 1 + self.calcular_complexidade_arvore(no.get('esquerda')) + \
               self.calcular_complexidade_arvore(no.get('direita'))
    
    def selecionar(self):
        """Seleciona indivíduos da população usando seleção por torneio"""
        tamanho_torneio = 3
        selecionados = []

        for _ in range(self.tamanho_populacao):
            # Seleciona aleatoriamente indivíduos para o torneio
            torneio = random.sample(self.populacao, tamanho_torneio)
            # Seleciona o melhor indivíduo do torneio
            vencedor = max(torneio, key=lambda x: x.fitness)
            selecionados.append(vencedor)

        return selecionados

    def evoluir(self, n_geracoes=15):
        for geracao in range(n_geracoes):
            print(f"\n🧬 Geração {geracao + 1}/{n_geracoes}")
            
            # Avaliação paralela
            resultados = self.avaliar_populacao_paralela()
            
            # Calcular métricas
            metricas = self.calcular_metricas_populacao()
            
            print(f"✨ Melhor fitness da geração: {self.melhor_fitness:.2f}")
            print(f"📊 Fitness médio: {metricas['fitness_medio']:.2f}")
            print(f"🌳 Diversidade: {metricas['diversidade']:.2f}")
            
            # Seleção e reprodução
            selecionados = self.selecionar()
            nova_populacao = [self.melhor_individuo]  # Elitismo
            
            while len(nova_populacao) < self.tamanho_populacao:
                pai1, pai2 = random.sample(selecionados, 2)
                filho = pai1.crossover(pai2)
                
                # Aplicar diferentes estratégias de mutação
                if random.random() < 0.33:
                    filho.arvore_aceleracao = EstrategiaMutacao.mutacao_adaptativa(
                        filho.arvore_aceleracao, 0.25, filho.fitness
                    )
                    filho.arvore_rotacao = EstrategiaMutacao.mutacao_adaptativa(
                        filho.arvore_rotacao, 0.25, filho.fitness
                    )
                elif random.random() < 0.66:
                    filho.arvore_aceleracao = EstrategiaMutacao.mutacao_estrutural(
                        filho.arvore_aceleracao, 0.25
                    )
                    filho.arvore_rotacao = EstrategiaMutacao.mutacao_estrutural(
                        filho.arvore_rotacao, 0.25
                    )
                else:
                    filho.mutacao(0.25)
                
                nova_populacao.append(filho)
            
            self.populacao = nova_populacao
            self.historico_fitness.append(self.melhor_fitness)
        
        # Plotar métricas finais
        self.plotar_metricas()
        
        return self.melhor_individuo, self.historico_fitness

    def plotar_metricas(self):
        plt.figure(figsize=(15, 10))
        
        # Plotar fitness médio e melhor
        plt.subplot(2, 2, 1)
        plt.plot(self.historico_fitness, label='Melhor Fitness')
        plt.title('Evolução do Fitness')
        plt.xlabel('Geração')
        plt.ylabel('Fitness')
        plt.legend()
        
        # Plotar diversidade genética
        plt.subplot(2, 2, 2)
        metricas = self.calcular_metricas_populacao()
        plt.plot([self.calcular_diversidade() for _ in range(len(self.historico_fitness))], 
                label='Diversidade Genética')
        plt.title('Diversidade Genética')
        plt.xlabel('Geração')
        plt.ylabel('Diversidade')
        
        # Plotar complexidade das árvores
        plt.subplot(2, 2, 3)
        plt.plot([self.calcular_complexidade_media() for _ in range(len(self.historico_fitness))], 
                label='Complexidade Média')
        plt.title('Complexidade das Árvores')
        plt.xlabel('Geração')
        plt.ylabel('Complexidade')
        
        plt.tight_layout()
        plt.savefig('metricas_evolucao.png')
        plt.close()

# =====================================================================
# PARTE 3: EXECUÇÃO DO PROGRAMA (PARA O ALUNO MODIFICAR)
# Esta parte contém a execução do programa e os parâmetros finais.
# =====================================================================

# Executando o algoritmo
if __name__ == "__main__":
    print("Iniciando simulação de robô com programação genética...")
    
    # Criar e treinar o algoritmo genético
    print("Treinando o algoritmo genético...")
    pg = ProgramacaoGeneticaParalela(tamanho_populacao=40, profundidade=5)
    melhor_individuo, historico = pg.evoluir(n_geracoes=15)
    
    # Salvar o melhor indivíduo
    print("Salvando o melhor indivíduo...")
    melhor_individuo.salvar('melhor_robo.json')
    
    # Simular o melhor indivíduo
    print("Simulando o melhor indivíduo...")
    ambiente = Ambiente()
    robo = Robo(ambiente.largura // 2, ambiente.altura // 2)
    simulador = Simulador(ambiente, robo, melhor_individuo)
    
    print("Executando simulação em tempo real...")
    print("A simulação será exibida em uma janela separada.")
    print("Pressione Ctrl+C para fechar a janela quando desejar.")
    simulador.simular() 