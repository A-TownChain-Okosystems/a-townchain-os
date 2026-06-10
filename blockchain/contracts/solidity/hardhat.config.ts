import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import * as dotenv from "dotenv";

dotenv.config();

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
    },
  },
  networks: {
    // Lokales Devnet
    hardhat: {
      chainId: 9000,
    },
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 9000,
    },
    // KAI-OS Devnet
    devnet: {
      url: process.env.DEVNET_RPC_URL || "http://127.0.0.1:8545",
      chainId: 9000,
      accounts: process.env.DEPLOYER_PRIVATE_KEY
        ? [process.env.DEPLOYER_PRIVATE_KEY]
        : [],
    },
    // Testnet
    testnet: {
      url: process.env.TESTNET_RPC_URL || "https://rpc.testnet.kai-os.io",
      chainId: 9000,
      accounts: process.env.DEPLOYER_PRIVATE_KEY
        ? [process.env.DEPLOYER_PRIVATE_KEY]
        : [],
    },
    // Ethereum Sepolia (für Bridge + wATC)
    sepolia: {
      url: `https://sepolia.infura.io/v3/${process.env.INFURA_KEY || ""}`,
      chainId: 11155111,
      accounts: process.env.DEPLOYER_PRIVATE_KEY
        ? [process.env.DEPLOYER_PRIVATE_KEY]
        : [],
    },
  },
  etherscan: {
    apiKey: process.env.ETHERSCAN_API_KEY || "",
  },
  paths: {
    sources:   "./",
    tests:     "../test",
    cache:     "./cache",
    artifacts: "./artifacts",
  },
};

export default config;
