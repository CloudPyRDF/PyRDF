import ROOT
from PyRDF.backend.Backend import Backend


class Local(Backend):
    """
    Backend that relies on the C++ implementation of RDataFrame to locally
    execute the current graph.

    Attributes:
        config (dict): The config object for the Local backend.
    """

    def __init__(self, config={}):
        """
        Creates a new instance of the
        Local implementation of `Backend`.

        Args:
            config (dict, optional): The config object for the required
                backend. The default value is an empty Python dictionary:
                :obj:`{}`.
        """
        super(Local, self).__init__(config)
        operations_not_supported = [
            'Take',
            'Snapshot',
            'Foreach',
            'Reduce',
            'Aggregate',
        ]
        if ROOT.ROOT.IsImplicitMTEnabled():
            # Add `Range` operation only if multi-threading
            # is disabled.
            operations_not_supported.append('Range')

        self.supported_operations = [op for op in self.supported_operations
                                     if op not in operations_not_supported]
        self.pyroot_rdf = None

    def execute(self, generator, trigger_loop=False):
        """
        Executes locally the current RDataFrame graph.

        Args:
            generator (PyRDF.CallableGenerator): An instance of
                :obj:`CallableGenerator` that is responsible for generating
                the callable function.

        """
        mapper = generator.get_callable()  # Get the callable

        # if the RDataFrame has not been created yet or if a new one
        # is created by the user in the same session
        if not self.pyroot_rdf or self.pyroot_rdf is not generator.head_node:
            self.pyroot_rdf = ROOT.ROOT.RDataFrame(*generator.head_node.args)

        values = mapper(self.pyroot_rdf)  # Execute the mapper function

        # Get the action nodes in the same order as values
        nodes = generator.get_action_nodes()

        for node, value in zip(nodes, values):
            # Set the obtained values and
            # 'RResultPtr's of action nodes
            if trigger_loop and hasattr(value, 'GetValue'):
                # Info actions do not have GetValue
                node.value = value.GetValue()
            # We store the 'RResultPtr's because,
            # those should be in scope while doing
            # a 'GetValue' call on them
            node.ResultPtr = value
