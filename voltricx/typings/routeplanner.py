# The MIT License (MIT)
#
# Copyright (c) 2026-Present @JustNixx, @Dipendra-creator and RevvLabs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from pydantic import Field

from .base import LavalinkBaseModel
from .enums import IPBlockType, RoutePlannerClass


class IPBlock(LavalinkBaseModel):
    type: IPBlockType
    size: str


class FailingAddress(LavalinkBaseModel):
    failing_address: str = Field(alias="failingAddress")
    failing_timestamp: int = Field(alias="failingTimestamp")
    failing_time: str = Field(alias="failingTime")


class RoutePlannerDetails(LavalinkBaseModel):
    ip_block: IPBlock = Field(alias="ipBlock")
    failing_addresses: list[FailingAddress] = Field(alias="failingAddresses")
    rotate_index: str | None = Field(None, alias="rotateIndex")
    ip_index: str | None = Field(None, alias="ipIndex")
    current_address: str | None = Field(None, alias="currentAddress")
    current_address_index: str | None = Field(None, alias="currentAddressIndex")
    block_index: str | None = Field(None, alias="blockIndex")


class RoutePlannerStatus(LavalinkBaseModel):
    planner_class: RoutePlannerClass | None = Field(None, alias="class")
    details: RoutePlannerDetails | None = None


class RoutePlannerFreeAddressPayload(LavalinkBaseModel):
    address: str
