PYTHON_VERSION := 3.9.7
VIRTUALENV_DIR := .venv
VIRTUALENV_ACTIVATE := $(VIRTUALENV_DIR)/bin/activate
RED='\033[1;91m'
NC='\033[0m' # No Color

define create_venv
	@if [[ -d "./${VIRTUALENV_DIR}" ]]; then \
		echo "Virtual env already exists"; \
	else \
		pyenv local ${PYTHON_VERSION}; \
		python3 -m venv ${VIRTUALENV_DIR}; \
		python3 -m pip install --upgrade pip; \
	fi
endef

define checkenv-command
	@printf "checking $(1)..." && (type $(1) && echo "ok") || (echo $(2) && exit 1)
endef

define install_packages
	source $(VIRTUALENV_ACTIVATE) &&  pip install -r requirements.txt
endef

.PHONY: clean build test runserver kube-ssh
.SILENT: build

warn:
	@echo "${RED} Please cp config.yaml.dist config.yaml # Check LastPass "XCover API – Dev config.yaml" ${NC} "

clean::
	@rm -rf $(VIRTUALENV_DIR) .cache .eggs .tmp *.egg-info ./*.egg-info
	@find . -name ".DS_Store" -exec rm -rf {} \; || true
	@find . -name "*.pyc" -exec rm -rf {} \; || true
	@find . -name "__pycache__" -exec rm -rf {} \; || true

build: warn
	$(call create_venv)
	$(call install_packages)

test: build
	source $(VIRTUALENV_ACTIVATE) && pytest -n auto

docker-run:
	docker-compose up -d
	source $(VIRTUALENV_ACTIVATE) && ./bin/reset_dev_db.sh

runserver: build
	source $(VIRTUALENV_ACTIVATE) && python manage.py migrate && python manage.py runserver

run:
	source $(VIRTUALENV_ACTIVATE) && python manage.py runserver

prepare-%:
	$(call checkenv-command,git-cliff,"Please install https://github.com/orhun/git-cliff")
	git cliff --latest -p CHANGELOG.md
	git add CHANGELOG.md
	git commit -m "Update CHANGELOG.md"
	git push -u origin HEAD

release-major: prepare-major

release-minor: prepare-minor

release-patch: prepare-patch

release::release-patch


