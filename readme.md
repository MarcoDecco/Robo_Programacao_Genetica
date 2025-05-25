# Projeto: Robô com Programação Genética

## Integrantes do Grupo
- Matheus Ribas  
- Marco Decco  
- Lucas Picanço  
- Rafael Portugal  

## 🎯 Objetivo

Desenvolver e aprimorar um robô que se locomove de forma autônoma em um ambiente 2D aleatório com obstáculos, recursos e uma meta final. Através de **programação genética**, o robô aprende a:

- Desviar de obstáculos
- Coletar recursos
- Economizar energia
- Chegar até a meta com eficiência

## 🧠 O que foi feito

1. **Estudo do código base** para entender as limitações iniciais.
2. **Melhorias no algoritmo genético**, com:
   - Penalidades para decisões ruins.
   - Recompensas para boas ações.
3. **Sistema de ilhas**: populações evoluindo separadamente.
4. **Injeção de diversidade** a cada 3 gerações.
5. **Verificações constantes** de comportamento para refinar as estratégias do robô.

## 🛠️ Alterações realizadas

- **Novos operadores matemáticos**: `sin`, `cos`, `log_safe`, para decisões mais suaves e cíclicas.
- **Sistema de ilhas e migração**: populações separadas, com troca de indivíduos bons entre elas.
- **Função de fitness reformulada**, agora avalia:
  - Coleta de recursos
  - Colisões
  - Gasto de energia
  - Movimentação no mapa
- **Aumento da profundidade das árvores de decisão**: até profundidade 5.
- **Aumento da taxa de mutação**: para explorar mais soluções e evitar estagnação.

## 🤔 Por que alteramos?

Durante os testes, o robô:
- Ficava preso em obstáculos
- Tentava ir direto à meta sem pegar recursos
- A população aprendia comportamentos ineficientes

As mudanças resolveram esses problemas, e o robô passou a:
- Tomar melhores decisões
- Desviar com mais precisão
- Economizar energia
- Evoluir com mais estabilidade

## 📈 Resultados

Com 15 gerações de evolução (antes eram apenas 5), observamos:
- Aumento constante no valor de fitness
- Robôs mais eficientes e inteligentes
- Menos colisões e melhor uso dos recursos

## 🔗 Links Importantes

- 📹 Vídeo do robô em ação: [YouTube](https://youtu.be/xEIEjlOH38E)  
- 💻 Repositório no GitHub: [https://github.com/MarcoDecco/Robo_Programacao_Genetica](https://github.com/MarcoDecco/Robo_Programacao_Genetica)

> Obs: Todos os commits foram realizados em branches. Apenas o melhor código foi mesclado na branch `master`.

## ✅ Conclusão

Este projeto foi uma experiência enriquecedora com algoritmos evolutivos. A partir de soluções aleatórias, conseguimos ensinar um robô a tomar decisões inteligentes com:

- Boa definição de fitness
- Estratégias de diversidade (ilhas, migração, mutação)
- Colaboração constante entre os membros

Foi recompensador tanto no aprendizado técnico quanto no trabalho em equipe.

---