// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
// ATCSwap.sol — A-TownChain AMM Liquidity Pool (Issue #45, Kap. 26)
// Constant Product Market Maker: x * y = k  |  0.30% Swap-Fee

interface IERC20Minimal {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract ATCLPToken {
    string  public name        = "ATC Liquidity Provider Token";
    string  public symbol      = "ATC-LP";
    uint8   public decimals    = 18;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    event Transfer(address indexed from, address indexed to, uint256 value);
    function _mint(address to, uint256 v) internal { totalSupply += v; balanceOf[to] += v; emit Transfer(address(0), to, v); }
    function _burn(address from, uint256 v) internal { balanceOf[from] -= v; totalSupply -= v; emit Transfer(from, address(0), v); }
    function transfer(address to, uint256 v) external returns (bool) { balanceOf[msg.sender] -= v; balanceOf[to] += v; emit Transfer(msg.sender, to, v); return true; }
    function transferFrom(address from, address to, uint256 v) external returns (bool) { allowance[from][msg.sender] -= v; balanceOf[from] -= v; balanceOf[to] += v; emit Transfer(from, to, v); return true; }
    function approve(address s, uint256 v) external returns (bool) { allowance[msg.sender][s] = v; return true; }
}

contract ATCSwap is ATCLPToken {
    IERC20Minimal public immutable tokenA;
    IERC20Minimal public immutable tokenB;
    uint256 public reserveA;
    uint256 public reserveB;
    uint256 public constant FEE_BPS     = 30;
    uint256 public constant MIN_LIQ     = 1_000;
    address public feeTo;

    event Swap(address indexed user, uint256 amtIn, uint256 amtOut, bool aToB);
    event AddLiquidity(address indexed lp, uint256 a, uint256 b, uint256 lp_tokens);
    event RemoveLiquidity(address indexed lp, uint256 a, uint256 b, uint256 lp_tokens);
    event Sync(uint256 rA, uint256 rB);

    constructor(address _tokenA, address _tokenB, address _feeTo) {
        tokenA = IERC20Minimal(_tokenA);
        tokenB = IERC20Minimal(_tokenB);
        feeTo  = _feeTo;
    }

    function getAmountOut(uint256 amtIn, uint256 rIn, uint256 rOut) public pure returns (uint256) {
        require(amtIn > 0 && rIn > 0 && rOut > 0, "INVALID");
        uint256 amtInFee = amtIn * (10_000 - FEE_BPS);
        return (amtInFee * rOut) / (rIn * 10_000 + amtInFee);
    }

    function swapAtoB(uint256 amtIn, uint256 minOut, address to) external returns (uint256 out) {
        out = getAmountOut(amtIn, reserveA, reserveB);
        require(out >= minOut, "SLIPPAGE");
        tokenA.transferFrom(msg.sender, address(this), amtIn);
        tokenB.transfer(to, out);
        reserveA += amtIn; reserveB -= out;
        emit Swap(msg.sender, amtIn, out, true);
        emit Sync(reserveA, reserveB);
    }

    function swapBtoA(uint256 amtIn, uint256 minOut, address to) external returns (uint256 out) {
        out = getAmountOut(amtIn, reserveB, reserveA);
        require(out >= minOut, "SLIPPAGE");
        tokenB.transferFrom(msg.sender, address(this), amtIn);
        tokenA.transfer(to, out);
        reserveB += amtIn; reserveA -= out;
        emit Swap(msg.sender, amtIn, out, false);
        emit Sync(reserveA, reserveB);
    }

    function addLiquidity(uint256 aDesired, uint256 bDesired, address to) external returns (uint256 a, uint256 b, uint256 lp) {
        if (reserveA == 0 && reserveB == 0) { a = aDesired; b = bDesired; }
        else {
            uint256 bOpt = (aDesired * reserveB) / reserveA;
            if (bOpt <= bDesired) { a = aDesired; b = bOpt; }
            else { a = (bDesired * reserveA) / reserveB; b = bDesired; }
        }
        tokenA.transferFrom(msg.sender, address(this), a);
        tokenB.transferFrom(msg.sender, address(this), b);
        if (totalSupply == 0) { lp = _sqrt(a * b) - MIN_LIQ; _mint(address(0), MIN_LIQ); }
        else { lp = _min((a * totalSupply) / reserveA, (b * totalSupply) / reserveB); }
        require(lp > 0, "ZERO_LP");
        _mint(to, lp);
        reserveA += a; reserveB += b;
        emit AddLiquidity(to, a, b, lp);
        emit Sync(reserveA, reserveB);
    }

    function removeLiquidity(uint256 lp, address to) external returns (uint256 a, uint256 b) {
        a = (lp * reserveA) / totalSupply;
        b = (lp * reserveB) / totalSupply;
        require(a > 0 && b > 0, "ZERO");
        _burn(msg.sender, lp);
        tokenA.transfer(to, a); tokenB.transfer(to, b);
        reserveA -= a; reserveB -= b;
        emit RemoveLiquidity(to, a, b, lp);
        emit Sync(reserveA, reserveB);
    }

    function getPrice() external view returns (uint256 pAinB, uint256 pBinA) {
        require(reserveA > 0 && reserveB > 0, "NO_LIQ");
        pAinB = (reserveB * 1e18) / reserveA;
        pBinA = (reserveA * 1e18) / reserveB;
    }

    function getReserves() external view returns (uint256, uint256) { return (reserveA, reserveB); }
    function setFeeTo(address _f) external { feeTo = _f; }

    function _sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) { z = y; uint256 x = y/2+1; while (x < z) { z = x; x = (y/x+x)/2; } }
        else if (y != 0) { z = 1; }
    }
    function _min(uint256 a, uint256 b) internal pure returns (uint256) { return a < b ? a : b; }
}
