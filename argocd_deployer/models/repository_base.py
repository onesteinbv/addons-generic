import logging

from odoo import models
from odoo.tools.safe_eval import safe_eval

ADD_FILES = "add"
REMOVE_FILES = "remove"

_logger = logging.getLogger(__name__)


class RepositoryBase(models.AbstractModel):
    _name = "argocd.repository.base"

    def _get_repository(self):
        """Get the repository and affected by this model."""
        raise NotImplementedError("Repository is not specified.")

    def _get_branch(self):
        """Get the repository and affected by this model."""
        raise NotImplementedError("Branch is not specified.")

    def _format_commit_message(self, message):
        """Apply formatting to the commit message."""
        return message

    @staticmethod
    def _get_remote(repository):
        """Find the provided repository's remote repository."""
        return repository.remotes.origin

    @staticmethod
    def _pull_from_repository(repository, branch, remote):
        """Switch to the correct branch, then execute a git pull on the
        repository."""
        repository.git.checkout(branch)
        repository.git.reset(
            "--hard", "origin/%s" % branch
        )  # Make sure we don't lock after failed push
        remote.pull()

    def _commit(self, repository, commit_message, files):
        if files and type(files) is dict and files.get(ADD_FILES):
            if type(files[ADD_FILES] is str):
                repository.index.add([files[ADD_FILES]])
            elif type(files[ADD_FILES] is list and len(files[ADD_FILES] > 0)):
                repository.index.add(files[ADD_FILES])
        if files and type(files) is dict and files.get(REMOVE_FILES):
            if type(files[REMOVE_FILES] is str):
                repository.index.remove([files[REMOVE_FILES]])
            elif type(files[REMOVE_FILES] is list and len(files[REMOVE_FILES] > 0)):
                repository.index.remove(files[REMOVE_FILES])
        repository.index.commit(self._format_commit_message(commit_message))

    def _apply_repository_changes(self, local_changes_callback):
        # TODO: Fix concurrency issue
        # TODO: add automatic healing if conflicts appear whatsoever
        self.ensure_one()
        is_simulation = safe_eval(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("argocd.simulate_commit", False)
        )
        repository = self._get_repository()
        branch = self._get_branch()
        remote = self._get_remote(repository)
        if not is_simulation:
            _logger.info(f"Pulling from repository {repository.working_dir}...")
            self._pull_from_repository(repository, branch, remote)
        files, message = local_changes_callback()

        if not is_simulation:
            _logger.info(f"Pushing to repository {repository.working_dir}...")
            self._commit(repository, message, files)
            remote.push()
