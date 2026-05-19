# shcedule_automation

# 🇮🇹 Prenota@Mi Auto-Booker & Monitor

Este projeto é uma automação assíncrona desenvolvida em Python com **Playwright** para monitorar e agendar serviços no portal **Prenota@Mi** (Consulados Italianos). O script simula o comportamento humano, evade detecções básicas de automação e gerencia quedas de servidor comuns do sistema.

> ⚠️ **Aviso de Isenção de Responsabilidade:** Este script foi desenvolvido apenas para fins de estudo e facilitação de uso pessoal. O uso de automações pode violar os Termos de Serviço do portal Prenota@Mi. Use por sua conta e risco.

---

## 🚀 Funcionalidades

* **Anti-Bot (Stealth Mode):** Utiliza a biblioteca `playwright-stealth` e perfis persistentes para reduzir as chances de bloqueio.
* **Ação Humana Automatizada:** Adiciona *jitter* (atrasos aleatórios) antes de interações e cliques para emular o comportamento humano.
* **Resiliência a Erros:** * Tratamento de Erros HTTP 500 (Servidor sobrecarregado) com recuo progressivo de tempo.
    * Detecção de bloqueios de firewall (**Radware**).
* **Interação Humano-Robô:** Detecta quando o site solicita re-verificação (Captcha, Logout, Expiração de Sessão), pausa a automação, emite um alerta sonoro (exclusivo para macOS) e aguarda a intervenção manual do usuário para retomar.
* **Sessão Persistente:** Salva o perfil do navegador localmente, evitando ter que fazer login do zero a cada execução.

---

## 🛠️ Pré-requisitos

Antes de começar, você precisará ter instalado em sua máquina:
* [Python 3.8+](https://www.python.org/)
* Navegador **Firefox** ou **Google Chrome** instalado.

---

## 📦 Instalação

1. Clone ou baixe este repositório para a sua máquina local.
2. Crie um ambiente virtual (opcional, mas recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Linux/macOS
   # ou
   .\venv\Scripts\activate  # No Windows
