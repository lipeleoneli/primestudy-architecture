# Atributos de Qualidade — PrimeStudy
**Norma de referência:** ISO/IEC 25010:2023  
**Autor:** Equipe PrimeStudy

---

## 1. Como os atributos foram identificados

Os atributos de qualidade prioritários foram escolhidos a partir de três fontes:
1. **Contexto do sistema:** plataforma web de estudo individual, com chamadas a APIs externas (Gemini, Firebase) de alta latência.
2. **Perfil dos usuários:** estudantes universitários que usam o sistema durante sessões de estudo, exigindo respostas rápidas e dados confiáveis.
3. **Restrições do time:** equipe pequena (6 pessoas), sem infraestrutura dedicada, prazo semestral — manutenibilidade é crítica.

---

## 2. Atributos Prioritários

### 2.1 Manutenibilidade (Maintainability)
**Subcaracterísticas relevantes (ISO 25010):** Modularidade, Reusabilidade, Modificabilidade.

**Por que é prioritário:**  
O código do PI V entregou tudo em um `app.py` de 435 linhas. Qualquer membro do time que precisasse adicionar um novo tipo de conteúdo gerado pela IA tinha que entender toda a função `gerar_conteudo()` de 120 linhas com 8 `elif`. Esse acoplamento elevado tornava cada mudança arriscada.

**Como a arquitetura atende:**  
- **Modularidade:** cada tipo de conteúdo é uma `ConteudoStrategy` independente. Adicionar "Podcast Script" = criar `PodcastScriptStrategy`, sem alterar nenhum arquivo existente (OCP).  
- **Reusabilidade:** `IEstudoRepository` pode ser reutilizada por qualquer camada que precise de dados de estudos, sem duplicar lógica de acesso ao Firestore.  
- **Modificabilidade:** trocar o Gemini por outro LLM exige implementar `IGeradorIA` em um novo adapter — os use cases e strategies não mudam.

**Métrica de verificação:** número de arquivos alterados para adicionar um novo tipo de conteúdo. Meta: **1 arquivo** (a nova Strategy + registro na Factory).

---

### 2.2 Testabilidade (Testability)
**Subcaracterística (ISO 25010):** Testabilidade.

**Por que é prioritário:**  
No PI V, testar a geração de conteúdo exigia uma chamada real à API do Gemini e um documento real no Firestore. Isso torna os testes lentos, custosos e dependentes de rede.

**Como a arquitetura atende:**  
- `IGeradorIA` e `IEstudoRepository` são interfaces ABC. Em testes, substituem-se por mocks que retornam respostas fixas.  
- Os use cases (`ProcessarPDFUseCase`, `GerarConteudoUseCase`) não importam nenhuma biblioteca externa — recebem tudo por injeção de dependência (DIP).  
- Resultado: é possível testar toda a lógica de negócio em milissegundos, sem internet.

**Métrica de verificação:** os testes em `tests/` executam sem variáveis de ambiente `GEMINI_API_KEY` ou `FIREBASE_*`.

---

### 2.3 Segurança — Confidencialidade (Security / Confidentiality)
**Subcaracterísticas (ISO 25010):** Confidencialidade, Autenticidade.

**Por que é prioritário:**  
O sistema armazena material de estudo pessoal. Um usuário não pode acessar dados de outro — isso é uma invariante de negócio, não uma feature opcional.

**Como a arquitetura atende:**  
- **Isolamento por UID:** toda query ao Firestore é prefixada com `usuarios/{uid}/` — nenhuma rota retorna dados sem validar o `uid` da sessão.  
- **Firebase Authentication:** tokens JWT com expiração gerenciados pelo Google. O backend Flask verifica o token a cada login e jamais confia em `uid` enviado pelo cliente.  
- **Sessão Flask server-side:** o `uid` fica na sessão do servidor; o cliente recebe apenas um cookie de sessão assinado.

**Métrica de verificação:** em modo de produção (real), toda rota `/api/*` retorna 401 se `session['uid']` não estiver presente. No modo demo, documentado no README, a verificação é dispensada (um `uid` fixo é usado) para permitir avaliação sem credenciais.

---

### 2.4 Eficiência de Desempenho (Performance Efficiency)
**Subcaracterísticas (ISO 25010):** Comportamento em relação ao tempo, Utilização de recursos.

**Por que é prioritário:**  
Chamadas à API do Gemini levam entre 3 e 15 segundos. Uma arquitetura que faz chamadas desnecessárias degrada a experiência do usuário de forma perceptível.

**Como a arquitetura atende:**  
- **Cache de conteúdo gerado:** o campo `conteudo` do estudo no Firestore armazena o resultado. Na próxima vez que o usuário abre o estudo, o conteúdo já existe — `GerarConteudoUseCase` só chama a IA se `estudo.tem_conteudo(tipo)` retornar `False`.  
- **Separação clara permite adicionar cache de camada:** como os use cases dependem de `IEstudoRepository`, é possível adicionar um `CachedEstudoRepository` (padrão Decorator/Proxy) sem alterar nenhum use case.

**Métrica de verificação:** o endpoint `GET /api/estudos/{id}/checklist` deve retornar em < 200ms quando a checklist já está salva (sem chamada ao Gemini).

---

### 2.5 Confiabilidade — Disponibilidade (Reliability / Availability)
**Subcaracterísticas (ISO 25010):** Maturidade, Tolerância a falhas.

**Por que é prioritário:**  
O Gemini pode retornar respostas malformadas ou falhar. O sistema precisa degradar graciosamente — não travar a interface do usuário.

**Como a arquitetura atende:**  
- `QuizStrategy._validar_e_limpar()` trata `JSONDecodeError` e retorna uma questão de erro válida em vez de propagar exceção.  
- `GerarConteudoUseCase` lança exceções tipadas (`ValueError`, `RuntimeError`) que as rotas Flask capturam e convertem em respostas JSON com código de erro adequado.  
- Firebase Firestore tem SLA de 99,99% — a disponibilidade do banco não é responsabilidade do time.

---

## 3. Mapeamento Atributo → Decisão Arquitetural

| Atributo de Qualidade | Decisão que o suporta | ADR |
|---|---|---|
| Manutenibilidade | Clean Architecture + Strategy + Factory | ADR-002 |
| Testabilidade | Ports (interfaces ABC) + Injeção de dependência | ADR-002 |
| Segurança | Firebase Auth + sessão server-side + UID em todas as queries | ADR-003 |
| Eficiência de Desempenho | Cache de conteúdo no Firestore; separação permite Decorator futuro | ADR-003 |
| Confiabilidade | Tratamento de erros nas Strategies; Firebase com SLA garantido | ADR-003 |
