from typing import TypeVar, Generic

T = TypeVar("T")


class ListNode(Generic[T]):
    def __init__(self, val: T = 0, next=None, prev=None):
        self.val: T = val
        self.next: ListNode[T] = next
        self.prev: ListNode[T] = prev


class LinkedList(Generic[T]):
    def __init__(self):
        self.head: ListNode[T] = None
        self.tail: ListNode[T] = None

    def list_to_linked(self, val_list: list[T]) -> list[ListNode[T]]:
        prev: ListNode[T] = None
        node_list: list[ListNode[T]] = []
        for val in val_list:
            new_node = ListNode[T](val, None, prev)
            node_list.append(new_node)
            if self.head is None:
                self.head = new_node
            if prev is not None:
                prev.next = new_node
            prev = new_node
        self.tail = prev
        return node_list

    def linked_to_list(self, reverse: bool = False) -> list[T]:
        val_list: list[T] = []
        if reverse:
            raise RuntimeError("TODO")
        cur = self.head
        while cur is not None:
            val_list.append(cur.val)
            cur = cur.next
        return val_list

    def insert_after(self, node: ListNode[T], new_val: T):
        new_node = ListNode[T](new_val, node, node.next)
        node.next = new_node
        new_node.prev = new_node
