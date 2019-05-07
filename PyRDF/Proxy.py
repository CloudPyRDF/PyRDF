from __future__ import print_function
from PyRDF.CallableGenerator import CallableGenerator
from abc import ABCMeta, abstractmethod
from PyRDF.Operation import Operation
from PyRDF.Node import Node
# Abstract class declaration
# This ensures compatibility between Python 2 and 3 versions, since in
# Python 2 there is no ABC class
ABC = ABCMeta('ABC', (object,), {})


class Proxy(ABC):
    """
    Abstract class for proxies objects. These objects help to keep track of
    nodes' variable assignment. That is, when a node is no longer assigned
    to a variable by the user, the role of the proxy is to show that. This is
    done via changing the value of the :obj:`has_user_references` of the
    proxied node from :obj:`True` to :obj:`False`.
    """
    def __init__(self, node):
        """
        Creates a new `Proxy` object for a given node.

        Args:
            proxied_node: The node that the current Proxy should wrap.
        """
        self.proxied_node = node

    @abstractmethod
    def __getattr__(self, attr):
        """
        Proxies have to declare the way they intercept calls to attributes
        and methods of the proxied node.
        """
        pass

    def __del__(self):
        """
        This function is called right before the current Proxy gets deleted by
        Python. Its purpose is to show that the wrapped node has no more
        user references, which is one of the conditions for the node to be
        pruned from the computational graph.
        """
        self.proxied_node.has_user_references = False


class ActionProxy(Proxy):
    """
    Instances of ActionProxy act as futures of the result produced
    by some action node. They implement a lazy synchronization
    mechanism, i.e., when they are accessed for the first time,
    they trigger the execution of the whole RDataFrame graph.
    """
    def __getattr__(self, attr):
        """
        Intercepts calls on the result of
        the action node.

        Returns:
            function: A method to handle an operation call to the
            current action node.
        """
        self._cur_attr = attr  # Stores the name of operation call
        return self._call_action_result

    def GetValue(self):
        """
        Returns the result value of the current action
        node if it was executed before, else triggers
        the execution of the entire PyRDF graph before
        returning the value.

        Returns:
            The value of the current action node, obtained after executing the
            current action node in the computational graph.
        """
        from . import current_backend
        if not self.proxied_node.value:  # If event-loop not triggered
            generator = CallableGenerator(self.proxied_node.get_head())
            current_backend.execute(generator)

        return self.proxied_node.value

    def _call_action_result(self, *args, **kwargs):
        """
        Handles an operation call to the current action node and returns
        result of the current action node.
        """
        return getattr(self.GetValue(), self._cur_attr)(*args, **kwargs)


class TransformationProxy(Proxy):
    """
    A proxy object to an non-action node. It implements acces to attributes
    and methods of the proxied node. It is also in charge of the creation of
    a new operation node in the graph.
    """

    def __getattr__(self, attr):
        """
        Intercepts calls to attributes and methods of the proxied node and
        returns the appropriate object(s).

        Args:
            attr (str): The name of the attribute or method of the proxied
                node the user wants to access.
        """

        from . import current_backend
        # if attr is a supported operation, start
        # operation and node creation
        if attr in current_backend.supported_operations:
            self.proxied_node._new_op_name = attr  # Stores new operation name
            return self._create_new_op
        else:
            try:
                return getattr(self.proxied_node, attr)
            except AttributeError as e:
                raise e

    def _create_new_op(self, *args, **kwargs):
        """
        Handles an operation call to the current node and returns the new node
        built using the operation call.
        """
        # Create a new `Operation` object for the
        # incoming operation call
        op = Operation(self.proxied_node._new_op_name, *args, **kwargs)

        # Create a new `Node` object to house the operation
        newNode = Node(operation=op, get_head=self.proxied_node.get_head)

        # Add the new node as a child of the current node
        self.proxied_node.children.append(newNode)

        # Return the appropriate proxy object for the node
        if op.is_action():
            return ActionProxy(newNode)
        else:
            return TransformationProxy(newNode)
