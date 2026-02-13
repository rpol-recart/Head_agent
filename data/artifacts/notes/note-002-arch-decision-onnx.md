---
id: "note-002"
type: architecture_decision
title: "ADR: выбор ONNX Runtime для инференса модели качества"
created_at: "2026-02-03T15:00:00"
updated_at: "2026-02-03T16:00:00"
author: "leader"
status: approved
priority: P2
project_id: "pred_quality"
tags: ["architecture", "onnx", "inference", "deployment"]
related_people: ["ivanov", "novikov"]
related_artifacts: ["tz-001"]
checklist_total: 3
checklist_done: 1
---

# ADR: ONNX Runtime для инференса модели качества

## Контекст
Модель предиктивного качества проката должна работать в real-time (< 500мс)
на сервере без GPU. Нужно выбрать runtime для инференса.

## Рассмотренные варианты

### Вариант A: PyTorch (JIT / TorchScript)
- **Плюсы:** нативный формат, простая конвертация
- **Минусы:** тяжёлый runtime (~800MB), медленный CPU-инференс для ResNet

### Вариант B: ONNX Runtime
- **Плюсы:** лёгкий (~50MB), оптимизирован для CPU, поддерживает квантизацию INT8
- **Минусы:** не все операции PyTorch поддержаны, нужна конвертация

### Вариант C: TensorRT
- **Плюсы:** максимальная скорость
- **Минусы:** требует GPU (NVIDIA), не подходит по ограничению ТЗ

## Решение
**Выбран: Вариант B — ONNX Runtime**

Обоснование:
1. Подходит под ограничение CPU-only
2. Бенчмарк Иванова: ResNet-18 через ONNX = 120мс vs PyTorch = 380мс на CPU
3. Новиков подтвердил совместимость с MLOps пайплайном (MLflow → ONNX → FastAPI)
4. Квантизация INT8 даст ещё +30% скорости если нужно

## Последствия
- Иванов добавляет шаг экспорта в ONNX в training pipeline
- Новиков настраивает CI для автоматической конвертации
- Тестировать на production-like железе перед деплоем

## Миграция
- [x] Экспорт ResNet-18 в ONNX — Иванов (готово)
- [ ] Экспорт ансамбля (CatBoost + ResNet) в единый pipeline — Иванов
- [ ] CI-шаг для ONNX-конвертации — Новиков
