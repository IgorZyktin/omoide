# -*- coding: utf-8 -*-
"""Object that textual output for daemons.
"""
from datetime import datetime

from pydantic import BaseSettings, BaseModel


class Column(BaseModel):
    """Column DTO."""
    name: str
    width: int
    alias: str


class Output:
    """Object that textual output for daemons."""

    def __init__(self, silent: bool) -> None:
        """Initialize instance."""
        self.silent = silent

        if silent:
            self.print = self.print_dummy
        else:
            self.print = print

        self.columns: list[Column] = []
        self._columns_map: dict[str, Column] = {}

    def add_columns(self, *args: Column) -> None:
        """Store columns setup."""
        self.columns.extend(args)
        self._extend_alias(*args)

    def _extend_alias(self, *args: Column) -> None:
        """Store additional aliases."""
        self._columns_map.update({
            column.alias: column
            for column in args
        })

    def print_dummy(self, *args, **kwargs) -> None:
        """Do nothing."""

    def print_config(self, config: BaseSettings) -> None:
        """Human-readable display of the given config."""
        if self.silent:
            return

        self.print('Config:')

        for i, (key, value) in enumerate(config.dict().items(), start=1):
            if isinstance(value, datetime):
                self.print(f'\t{i:02d}. {key}=<{value}>')
            else:
                self.print(f'\t{i:02d}. {key}={value!r}')

    def print_line(self) -> None:
        """Print separation line for a table."""
        if self.silent:
            return

        segments = [
            '-' * column.width
            for column in self.columns
        ]

        self.print('+' + '+'.join(segments) + '+')

    def print_header(self) -> None:
        """Print header for the table."""
        if self.silent:
            return

        segments = [
            column.name.center(column.width)
            for column in self.columns
        ]

        self.print('|' + '|'.join(segments) + '|')

    def print_row(self, **kwargs: str) -> None:
        """Print table row."""
        if self.silent:
            return

        segments = []

        for key, value in kwargs.items():
            column = self._columns_map[key]
            text = value.center(column.width)
            segments.append(text)

        self.print('|' + '|'.join(segments) + '|')
