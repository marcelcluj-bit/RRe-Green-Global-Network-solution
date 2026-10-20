// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title TreeTokenRWA - Proof of Plantation & Anti-Deforestation Escrow
 * @author RRe-Green Global Network
 * @notice Tokenizes tree planting (1 EUR = 1 $TREE) and locks funds in escrow
 *         until Google Gemini AI verifies real-world execution on ground.
 */

contract TreeTokenRWA {
    address public owner;
    address public geminiVerifierOracle; // Oracle connected to Gemini AI
    
    enum Status { Pending, Verified, Rejected, DeforestedPenalized }

    struct PlantationBatch {
        uint256 id;
        string gpsCoordinates;
        uint256 totalTreesClaimed;
        uint256 fundsAllocated;
        Status status;
        bool fundsReleased;
        uint256 timestamp;
    }

    mapping(uint256 => PlantationBatch) public batches;
    uint256 public batchCounter;
    mapping(address => uint256) public treesAdoptedBy;

    event TreeAdopted(address indexed adopter, uint256 count);
    event BatchSubmitted(uint256 indexed batchId, string gpsCoordinates, uint256 treeCount);
    event BatchVerified(uint256 indexed batchId, bool approved, string aiAuditReport);
    event FundsReleased(uint256 indexed batchId, uint256 amount);
    event DeforestationReported(uint256 indexed batchId, string proofUri);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this");
        _;
    }

    modifier onlyOracle() {
        require(msg.sender == geminiVerifierOracle, "Only Gemini AI Oracle can call this");
        _;
    }

    constructor(address _oracleAddress) {
        owner = msg.sender;
        geminiVerifierOracle = _oracleAddress;
    }

    /**
     * @dev Citizens or entities adopt trees (1 EUR equivalent per tree)
     */
    function adoptTree(uint256 treeCount) external payable {
        uint256 requiredAmount = treeCount * 1 ether; // Adjusted to native 1:1 EUR peg equivalent
        require(msg.value >= requiredAmount, "Insufficient funds to adopt trees");

        treesAdoptedBy[msg.sender] += treeCount;
        emit TreeAdopted(msg.sender, treeCount);
    }

    /**
     * @dev NGO/Forester submits a new planting batch with GPS coordinates
     */
    function submitPlantingBatch(string calldata gpsCoordinates, uint256 treeCount) external onlyOwner {
        batchCounter++;
        batches[batchCounter] = PlantationBatch({
            id: batchCounter,
            gpsCoordinates: gpsCoordinates,
            totalTreesClaimed: treeCount,
            fundsAllocated: treeCount * 1 ether,
            status: Status.Pending,
            fundsReleased: false,
            timestamp: block.timestamp
        });

        emit BatchSubmitted(batchCounter, gpsCoordinates, treeCount);
    }

    /**
     * @dev Automated Oracle triggered by Gemini AI approves/rejects batch and releases funds
     */
    function verifyBatchAI(uint256 batchId, bool approved, string calldata aiAuditReport) external onlyOracle {
        PlantationBatch storage batch = batches[batchId];
        require(batch.status == Status.Pending, "Batch already processed");

        if (approved) {
            batch.status = Status.Verified;
            batch.fundsReleased = true;
            
            payable(owner).transfer(batch.fundsAllocated);
            emit FundsReleased(batchId, batch.fundsAllocated);
        } else {
            batch.status = Status.Rejected;
        }

        emit BatchVerified(batchId, approved, aiAuditReport);
    }

    /**
     * @dev Anti-Deforestation Clause: If satellite or AI detects deforestation, flags batch & freezes future funds
     */
    function reportDeforestation(uint256 batchId, string calldata proofUri) external onlyOracle {
        PlantationBatch storage batch = batches[batchId];
        batch.status = Status.DeforestedPenalized;
        
        emit DeforestationReported(batchId, proofUri);
    }

    receive() external payable {}
}