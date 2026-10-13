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
