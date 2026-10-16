# Reprodução de experimentos

Esta pasta reúne material portátil para reproduzir avaliações com modelos.
Os testes unitários do gateway ficam em `desenvolvimento/gateway/testes/`;
as ferramentas de preparação e análise ficam em
[desenvolvimento/avaliacao-sentry/](../desenvolvimento/avaliacao-sentry/README.md).

- [Bateria portátil Sentry 1.0.0](sentry-1.0/README.md): 24 variantes, 48
  revisões principais, referências e dados fictícios congelados.

O conteúdo de `sentry-1.0/` é conferido por seu `SHA256.json`. Não altere
casos, scripts ou hashes para reorganizar pastas. Os quatro arquivos de
dados que haviam recebido CRLF foram restaurados aos bytes LF originais;
os hashes esperados permaneceram iguais. Os atributos na raiz do projeto
evitam nova conversão de textos no checkout Windows.

Para conferir sem executar modelos ou variantes:

```powershell
python -B reproducao-experimentos/sentry-1.0/scripts/bateria.py verificar
```

Renomear a pasta externa não transforma a bateria 1.0.0 em uma bateria da
versão atual. Consulte seu README para os requisitos e limites de reprodução.

## Complemento Sentry 1.3.1

[Pacote da campanha 1.3.1](sentry-1.3.1/README.md): instala o wheel 1.3.1, reutiliza os casos congelados e oferece preparação Windows, requisitos para outro ambiente, checklist de auditoria e seleção explícita de tentativas. Configurações: Luna low/medium/high e Sol 6.1 low. Registra também a compatibilidade LF/CRLF dos textos históricos sem reescrever seu manifesto.

```powershell
python -B reproducao-experimentos/sentry-1.3.1/scripts/bateria.py verificar
```

[Resultados e limitações](../pesquisa/02_resultados/COMPARACAO_SENTRY_131.md).
