# Makefile - Frente 1 (baseline e perfilamento) + infraestrutura de validação
# Uso: make help

CXX      ?= g++
CXXFLAGS ?= -O2
MPICXX   ?= mpicxx
NPS      := 1 2 3 4
BIN      := bin
SIZES    := 1000 2000 4000 8000
PASSOS   := 10

.PHONY: all help seq prof valid refs check baseline perfil mpi check-mpi medicao-mpi graficos-mpi clean

all: seq mpi

help:
	@echo "Alvos disponíveis:"
	@echo "  make seq       compila o sequencial de referência (06_nbody)"
	@echo "  make prof      compila a cópia com cronômetros (06_nbody_prof)"
	@echo "  make valid     compila o validador de estado final (06_nbody_valid)"
	@echo "  make refs      gera as referências validacao/ref_N.txt"
	@echo "  make check     compara uma nova execução com as referências"
	@echo "  make baseline  mede o baseline (resultados/baseline.csv)"
	@echo "  make perfil    mede a divisão forças/atualização (resultados/perfil.txt)"
	@echo "  make mpi       compila a versão MPI (06_nbody_mpi)"
	@echo "  make check-mpi valida a versão MPI contra as referências com -np $(NPS)"
	@echo "  make medicao-mpi mede seq + MPI (resultados/mpi.csv)"
	@echo "  make graficos-mpi gera resumo e gráficos (precisa de matplotlib)"
	@echo "  make clean     remove binários e arquivos temporários"

$(BIN):
	mkdir -p $(BIN)

$(BIN)/06_nbody: sequencial/06_nbody.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

$(BIN)/06_nbody_prof: sequencial/06_nbody_prof.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

$(BIN)/06_nbody_valid: validacao/06_nbody_valid.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

$(BIN)/06_nbody_mpi: mpi/06_nbody_mpi.cpp | $(BIN)
	$(MPICXX) $(CXXFLAGS) -o $@ $<

seq: $(BIN)/06_nbody
prof: $(BIN)/06_nbody_prof
valid: $(BIN)/06_nbody_valid
mpi: $(BIN)/06_nbody_mpi

# Referências: estado final (x, y, vx, vy) com 17 dígitos para cada N
refs: valid
	@for N in $(SIZES); do \
	  ./$(BIN)/06_nbody_valid $$N $(PASSOS) validacao/ref_$$N.txt; \
	done

# Validação: uma nova execução deve ser idêntica bit a bit à referência
check: valid
	@mkdir -p validacao/tmp
	@for N in $(SIZES); do \
	  ./$(BIN)/06_nbody_valid $$N $(PASSOS) validacao/tmp/teste_$$N.txt > /dev/null; \
	  bash validacao/compara.sh validacao/ref_$$N.txt validacao/tmp/teste_$$N.txt || exit 1; \
	done
	@rm -rf validacao/tmp

# Validação MPI: o estado final deve ser idêntico bit a bit para qualquer -np
check-mpi: mpi
	@mkdir -p validacao/tmp
	@for N in $(SIZES); do for P in $(NPS); do \
	  mpirun -np $$P ./$(BIN)/06_nbody_mpi $$N $(PASSOS) validacao/tmp/mpi_$$N.txt > /dev/null; \
	  echo -n "np=$$P "; bash validacao/compara.sh validacao/ref_$$N.txt validacao/tmp/mpi_$$N.txt || exit 1; \
	 done; done
	@rm -rf validacao/tmp

# Medição MPI: escalabilidade forte e fraca, mesmo protocolo do baseline
medicao-mpi: seq mpi
	bash scripts/medicao_mpi.sh

graficos-mpi:
	python3 scripts/graficos_mpi.py

# Baseline: 1 aquecimento descartado + 5 repetições por N (script do protocolo)
baseline: seq
	bash scripts/medicao.sh

# Perfilamento: mesmo protocolo, com a saída do binário de cronômetros
perfil: prof
	@mkdir -p resultados
	@for N in $(SIZES); do \
	  ./$(BIN)/06_nbody_prof $$N $(PASSOS) > /dev/null; \
	  for r in 1 2 3 4 5; do \
	    echo "rep=$$r N=$$N"; \
	    ./$(BIN)/06_nbody_prof $$N $(PASSOS); \
	  done; \
	done > resultados/perfil.txt
	@cat resultados/perfil.txt

clean:
	rm -rf $(BIN) validacao/tmp