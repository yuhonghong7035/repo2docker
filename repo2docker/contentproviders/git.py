import subprocess
import sys

from .base import ContentProvider, ContentProviderException
from ..utils import execute_cmd, check_ref


class Git(ContentProvider):
    """Provide contents of a remote git repository."""

    def detect(self, source, ref=None, extra_args=None):
        # Git is our content provider of last resort. This is to maintain the
        # old behaviour when git and local directories were the only supported
        # content providers. This means that this content provider will always
        # match. The downside is that the call to `fetch()` later on might fail
        return {'repo': source, 'ref': ref}

    def fetch(self, spec, output_dir, yield_output=False):
        repo = spec['repo']
        ref = spec.get('ref', None)

        # make a, possibly shallow, clone of the remote repository
        try:
            cmd = ['git', 'clone', '--recursive']
            if ref is None:
                cmd.extend(['--depth', '1'])
            cmd.extend([repo, output_dir])
            for line in execute_cmd(cmd, capture=yield_output):
                yield line

        except subprocess.CalledProcessError as e:
            msg = "Failed to clone repository from {repo}.".format(repo=repo)
            raise ContentProviderException(msg) from e

        # check out the specific ref given by the user
        if ref is not None:
            hash = check_ref(ref, output_dir)
            if hash is None:
                self.log.error('Failed to check out ref %s', ref,
                               extra=dict(phase='failed'))
                raise ValueError(f'Failed to check out ref {ref}')
            # If the hash is resolved above, we should be able to reset to it
            for line in execute_cmd(['git', 'reset', '--hard', hash],
                                    cwd=output_dir,
                                    capture=yield_output):
                yield line
