from sphinx import addnodes
from sphinx.domains.python import PyClassmember


class PyCoroutine(PyClassmember):
    def handle_signature(self, sig, signode):
        ret = super().handle_signature(sig, signode)
        signode.insert(0, addnodes.desc_annotation("coroutine ", "coroutine "))
        return ret

    def run(self):
        self.name = "py:method"
        return PyClassmember.run(self)


class PyAbstractCoroutine(PyCoroutine):
    def handle_signature(self, sig, signode):
        ret = super().handle_signature(sig, signode)
        signode.insert(
            0, addnodes.desc_annotation("abstractmethod ", "abstractmethod ")
        )
        return ret

    def run(self):
        self.name = "py:method"
        return PyClassmember.run(self)


def setup(app):
    app.add_directive_to_domain("py", "coroutine", PyCoroutine)
    app.add_directive_to_domain("py", "abstractcoroutine", PyAbstractCoroutine)
