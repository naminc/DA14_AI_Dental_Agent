@echo off
:: ============================================================
::  Ollama Optimized Startup Script
::  Cau hinh toi uu toc do cho Ollama local LLM
:: ============================================================

:: [1] GPU Offload - Day tat ca layers len GPU (NVIDIA)
set OLLAMA_NUM_GPU=999

:: [2] Flash Attention - Tang toc attention computation
set OLLAMA_FLASH_ATTENTION=1

:: [3] Keep Alive - Giu model trong RAM/VRAM 60 phut (tranh cold start)
set OLLAMA_KEEP_ALIVE=60m

:: [4] Parallel Requests - Cho phep 3 request dong thoi
set OLLAMA_NUM_PARALLEL=3

:: [5] Chi load 1 model (tiet kiem VRAM)
set OLLAMA_MAX_LOADED_MODELS=1

:: Khoi dong Ollama
echo ============================================================
echo   Ollama Optimized Configuration:
echo     OLLAMA_NUM_GPU         = %OLLAMA_NUM_GPU%
echo     OLLAMA_FLASH_ATTENTION = %OLLAMA_FLASH_ATTENTION%
echo     OLLAMA_KEEP_ALIVE      = %OLLAMA_KEEP_ALIVE%
echo     OLLAMA_NUM_PARALLEL    = %OLLAMA_NUM_PARALLEL%
echo     OLLAMA_MAX_LOADED_MODELS = %OLLAMA_MAX_LOADED_MODELS%
echo ============================================================
echo.

ollama serve
