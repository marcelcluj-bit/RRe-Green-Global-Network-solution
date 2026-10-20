// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title TreeTokenRWA - Proof of Plantation & Anti-Deforestation Escrow
 * @author Marcel (marcelcluj-bit)
 * @notice Tokenizeaza sadirea de copaci (1 EUR = 1 $TREE) si blocheaza fondurile 
 *         pana cand AI-ul Gemini confirma plantarea efectiva in teren.
 */

interface IERC20 {
    function mint(address to, uint256 amount) external;
}

contract TreeTokenRWA {
    address public owner;
    address public geminiVerifierOracle; // Adresa oracle-ului conectat la Gemini AI
    uint256 public constant TREE_PRICE_EUR = 1e18; // 1 EUR per copac (in wei equivalent)
    
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
     * @dev Adopta un copac cu 1 EUR (sau echivalent Stablecoin/Native)
     */
    function adoptTree(uint256 treeCount) external payable {
        // Asiguram finantarea transparenta
        uint256 requiredAmount = treeCount * 1 ether; // Ajustabil in functie de peg 1 EUR
        require(msg.value >= requiredAmount, "Suma insuficienta pentru adoptie");

        treesAdoptedBy[msg.sender] += treeCount;
        emit TreeAdopted(msg.sender, treeCount);
    }

    /**
     * @dev ONG-ul/Padurarul raporteaza un lot de arbori plantati in teren cu GPS
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
     * @dev Oracle-ul automatizat rulat de Gemini AI verifica pozele si aproba eliberarea banilor
     */
    function verifyBatchAI(uint256 batchId, bool approved, string calldata aiAuditReport) external onlyOracle {
        PlantationBatch storage batch = batches[batchId];
        require(batch.status == Status.Pending, "Lotul a fost deja procesat");

        if (approved) {
            batch.status = Status.Verified;
            batch.fundsReleased = true;
            
            // Banii sunt eliberati catre ONG doar daca AI-ul a confirmat plantarea pe teren
            payable(owner).transfer(batch.fundsAllocated);
            emit FundsReleased(batchId, batch.fundsAllocated);
        } else {
            batch.status = Status.Rejected;
        }

        emit BatchVerified(batchId, approved, aiAuditReport);
    }

    /**
     * @dev Clauza Anti-Taiere: Daca satelitul/AI-ul detecteaza defrisari, blocheaza contul
     */
    function reportDeforestation(uint256 batchId) external onlyOracle {
        PlantationBatch storage batch = batches[batchId];
        batch.status = Status.DeforestedPenalized;
    }

    receive() external payable {}
}
